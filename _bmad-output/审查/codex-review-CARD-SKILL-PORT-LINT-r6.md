> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r6.md)"`
> 审查绑定: `a709856a`（D-15 上限后由用户授权继续；Codex 自证审计期间 HEAD 已推进到 `ee4d0913`，其结论均早于第六条判据）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: …/worktrees/card-u4-hosts`(:6) / `model: gpt-6-astra`(:7) · `sandbox: read-only`(:10) · `reasoning effort: ultra`(:11)

---

复核绑定 **`a709856a`**，测试文件对象为 `ce68fcd0ce8440fe2164be4988406ddc3004a4bf`，共 1729 行。审计期间出现外部修改，收尾采样 HEAD 已推进到 `ee4d0913`；以下证据全部从指定 diff 在内存重建 **`a709856a`** 后复验。未修改文件、运行 pytest、读取禁读正文或连接服务。

**BLOCKER：未发现。**

**HIGH：按根因归并为 4 类。**

1. **HIGH — [test_skill_portability_lint.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:310)、`:329–338、345、445`：解析出的字符串片段不能代替表达式结果，静态可确定的越界仍会漏检。**

   在 Python fence 中，将 `P = "/tmp/cls-exam/x"` 单行替换为以下任一项：

   ```python
   P = f"/tmp/cls-exam/{'.'}./x"
   P = "/tmp/cls-exam/%s./x" % "."
   P = "/tmp/cls-exam/{}./x".format(".")
   P = "".join(("/tmp/cls-exam/", ".", "./x"))
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   P = "/tmp/cls-exam/" + "."[0] + "./x"
   P = "/tmp/cls-exam/" + ".x"[:1] + "./x"
   ```

   **七项均实测：九项计数不变，越界与可疑行均 `[] → []`；实际结果全部规范化为 `/tmp/x`。** 没有未知变量，不能归入“静态不可判”。

   shell 同样存在表达式层缺口：

   ```sh
   cp "/tmp/cls-exam/"`printf .`"./x" out
   ```

   相比安全路径，三项签名仍完全相同；`shlex` 将命令替换拆成普通词，源码又没有 `$` 或连续 `..`，可疑行不触发。即使把命令替换归为运行期展开，**“由可疑行兜底”也未覆盖反引号形式**。

2. **HIGH — [test_skill_portability_lint.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:370)、`:374–376`：Python 解析成功不等于采用了正确语言语义。**

   在 JSON fence 中，将安全路径替换为：

   ```json
   {"path":"/tmp/cls-exam/\u002e\u002e\/x"}
   ```

   `json.loads()` 得到 `/tmp/cls-exam/../x`，规范化为 `/tmp/x`；`_py_strings()` 却保留 `\/` 中的反斜杠，得到 `/tmp/cls-exam/..\/x` 并放行。**九计数及两附加集合均不变。** 当前解释器会发出 `SyntaxWarning`，但解析成功。

   不依赖该 warning 的 shell 反例：

   ```sh
   P='\
   /tmp/cls-exam/x'
   ```

   Python 消除反斜杠换行，认为路径合规；shell 单引号保留它们，实际值是命名空间外的相对路径。与安全赋值加一行注释的对照相比，三项签名仍相同。

3. **HIGH — [test_skill_portability_lint.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:297)、`:370–376`：逐物理行降级及未去除 Markdown 缩进，会丢失原本可解析的 Python／shell 语义。**

   在 bash fence 的 heredoc 中：

   ```sh
   python3 - <<'PYEOF'
   P = "/tmp/cls-exam/" + \
       "." "./x"
   PYEOF
   ```

   整块 AST 失败；赋值首行的单行 AST、shlex 均失败，次行不含 `/tmp`，因此越界为空。可疑行虽然合并续行，源码仍无连续 `..`，也为空。与相同行数的安全赋值对照相比，**九计数和两附加集合完全相同**；提取 heredoc 内完整 Python 后则明确得到 `/tmp/cls-exam/../x`。

   普通列表内的缩进 fence 也会复发：两格缩进的 `P = "/tmp/cls-exam/\x2e\x2e/x"` 因 `UnexpectedIndent` 降到 shlex，转义未还原，三项签名仍与安全值相同。

4. **HIGH — [test_skill_portability_lint.py:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:266)、`:285、294`：fence 边界仍会删除实际内容或将代码误当散文。**

   最小反例是位于行首的同行代码 span：

   ````text
   ```/tmp/cls-exam/../x```
   ````

   实现返回 `[(2, [], True)]`，整行内容被删除；相较安全的 `/tmp/cls-exam/x`，**九计数相同，越界与可疑行都为空**。

   同根另外两种已复现：

   - ` ```not-a-close` 带尾随文字仍被当作 closing fence；放在 Python 三引号字符串内时，会使后续越界赋值降成散文。
   - 合法列表首行 `- ```python` 未识别，后续代码同样漏过。

   三种形态均有安全／越界等计数对照。

上述单路径反例的九项向量均为：

```text
(0, 0, 0, 1, 1, 0, 0, 0, 0)
```

这些证明的是判据贡献等值，没有声称执行过整树测试。

**MEDIUM：1 条续存盲区。**

5. **MEDIUM — [test_skill_portability_lint.py:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:358)、`:666`：已登记 `/tmp` 可被重复使用而不要求登记，r5 此项仍在。**

   已有“禁写 `/tmp`”的文本末尾新增 Python fence `P = "/tmp"`，实测九计数不变，越界仍只有 `/tmp`，可疑行仍为空。原因是正文只计 `/tmp/`，候选又去重；这属于静态漏检，集合语义声明没有完整说明其后果。

**LOW：断言与行号边界。**

6. **LOW — [test_skill_portability_lint.py:1509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1509)：跨行负控由假越界候选承重，不能证明拼接语义正确。**

   在同一 heredoc 包装中，后缀为 `"../exam-candidates.json"` 或安全的 `"exam-candidates.json"`，越界结果都精确等于：

   ```text
   [('(/tmp/cls-exam/', '(/tmp/cls-exam')]
   ```

   红来自 shlex 把 Python 开括号并入路径。该断言能证明解析分支参与，但不能区分安全拼接与越界拼接；`:1513` 的行号位移代红限制也仍在。

7. **LOW — [test_skill_portability_lint.py:1609](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1609)：四反引号用例未验证“同字符”。**

   内存删除闭合条件中的同字符判断后，现有三条断言仍全部通过。此外，`:1604` 仍接收未使用的 `sandbox` 参数，正常 pytest 运行时仍会触发复制 fixture。

8. **LOW — [test_skill_portability_lint.py:1538](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1538)：参数表缺少 shell 单引号反斜杠回归样本。**

   实际是 **4 条参数行**，不是 5；加 HIGH-1、`~~~`、四反引号，共 **7 个执行案例**。原 shell 单引号反例当前已拦，但没有对应新增回归保护。

9. **LOW — [test_skill_portability_lint.py:1063](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1063)、`:1090`：r5 的分号断言不承重问题仍在。**

   内存把候选在分号处截断、丢掉目标 `/x` 后，覆盖表仍 **16/16 通过**，因为截断后的原路径本身已经越界。

10. **LOW — [test_skill_portability_lint.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:399)、`:413–419`：相邻独立 fence 仍可能被合成一条可疑逻辑行。**

    两个块分别包含 `"/tmp/cls-exam/x"`、`"$REL"`，实测被合并并误报行号 `2`。v3 越界判据已脱离它，因此此处确认的是误报。

其余要求逐项结论：

| 维度 | 复核结果 |
|---|---|
| 4 条新增参数负控 | **未发现**前提空跑或其他判据代打红。 |
| HIGH-1 纯函数及验伪锚 | **未发现**失效；移除 shell 候选后，精确路径断言立即失败。 |
| `~~~` 负控、四反引号长度判断 | **未发现**对应分支失效。 |
| 普通未闭合 fence 到 EOF | **未发现**漏检；保持代码上下文并抓到越界。 |
| `$'…'` | shlex 不还原其转义；普通样本会被 `$` 可疑行判据拦下，**未发现该样本三判据同时放行**。 |
| `_fence_blocks` 与 `_logical_lines` 行号算术 | **未发现**偏一错误；合成物理行 `98`／`577` 均正确返回。 |
| 现有 `[577]`／`[98]` | `577` 可从指定 diff 定位为变更记录行；`98` 正文禁读，**不能声称独立复算其现有上下文**。 |
| frontmatter、scripts、交接常量 | 限定材料中**未发现新增问题**；正式交接纯函数返回空违规列表。 |

收尾判断：**残余风险尚未完整声明，仍包含可静态确定的漏检，不能认定只剩保守误报与运行期不确定性。**

**本轮 BLOCKER 0 条，HIGH 4 条。**
