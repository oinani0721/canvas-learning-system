复核绑定 **`51282213e7ebd3d961bd8660f9ad138d761c9094`**；测试文件 blob 为 `944f8c0c67fe7814458af511c64a4289b17c9041`，收尾时工作区文件与提交一致。全程只读，未跑 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：6 条，按根因合并。** 以下各条主反例均经完整纯函数入口复现：与安全对照相比，**九项计数相同，五项路径附加判据及 URL 覆盖判据全部为 `[] → []`**。

1. **HIGH — [test_skill_portability_lint.py:695](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:695)、`:760`：去掉探针后，heredoc 结束标记可以使已经解析成功的 Python 语句被丢弃，属于新回归。**

   将下面内容放进 `sh` fence：

   ```sh
   python3 - <<'else'
   if False:
       pass
   elif P := "/tmp/cls-exam/" "." "./x":
       pass
   else
   echo done
   ```

   Python 实际设置的路径规范化为 `/tmp/x`；结束标记 `else` 却被当作续接，最终退回 shell 分词并丢掉拼接关系。安全对照仅将 `"."` 改为 `"a"`。

   内存恢复 diff 中的旧探针后，越界与动态判据均报红，确认**旧红、新漏**。同根成本回归也已复现：重复 1000 行合法的 `case = 0` 被合成一个单元，冷耗时约 **4.05 秒**，旧探针约 **0.044 秒**。

2. **HIGH — [test_skill_portability_lint.py:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:451)、`:1077`：新 `_shell_words()` 仍不能保留真实 shell 词，空白与转义整改不完整。**

   两个独立反例：

   ```text
   执行 P="/var/cache" "/tmp/cls-exam/x"
   执行 P="/var/cache \" /tmp/cls-exam/x"
   ```

   第一行两段引号之间是 **NBSP**，换成 U+3000 同样漏检：正则中的 `\s` 仍按 Unicode 空白切词。第二行的 `\"` 被误当闭合引号，含 `/tmp` 的片段丢失越界前缀及反斜杠。

   两行都是合法的 shell 赋值形态，值均以 `/var/cache` 开头；安全对照为 `执行 P="/tmp/cls-exam/x"`。

3. **HIGH — [test_skill_portability_lint.py:475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:475)：新分词器丢弃分隔空白，但调用方仍假定每词间只有一个字符，造成原文坐标失真。**

   精确构造：

   ```python
   '执行' + ' ' * 40 + 'P="/tmp/cls-exam/"`printf .`"./x"'
   ```

   实际路径为 `/tmp/x`。一个空格时 opaque 报红，40 个空格时全部漏检。`:476–477` 的 `pos += len(word) + 1` 不能还原真实位置；这是本轮替换分词方式带来的回归。

4. **HIGH — [test_skill_portability_lint.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:291)、`:372`、`:393`：closing 错把 opening 自身缩进算成额外额度，能提前闭合围栏，属于新回归。**

   第三行有四个空格：

   ````text
      ```python
   A = 1
       ```
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ```
   ````

   四空格标记应留在围栏内容中，实现却因 `4 <= open_indent + 3` 将其闭合，后续赋值落入散文。安全对照仅将 `"." * 2` 改成 `"."`；旧版能抓到坏形态，新版全部漏掉。

   **tab 同根有问题**：实现计字符数而非展开后的列数。零缩进 opening 配一个 tab 的 closing 会误闭合；`-\t` opening 又可能使合法 closing 闭不上。

5. **HIGH — [test_skill_portability_lint.py:492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:492)、`:536`：块边界行保留后没有正确处理其结束，既会多拼段，也会误拆段，属于新回归。**

   ```text
   # 标题 `未闭合
   执行 `/var/cache(
   /tmp/cls-exam/x`
   ```

   标题是独立块，但实现仅在标题前 `flush()`，标题中的反引号因此抢走正文 span 的 opening。旧版能提取越界路径，新版五集合全空。

   反方向同样成立：

   ```text
   执行 `/var/cache(
   1234567890. /tmp/cls-exam/x`
   ```

   十位数字不是合法 CommonMark 列表 marker，新正则却强制断段并丢失跨行 span。HTML 注释结束后继续拼段也存在同类漏检，但该情形是既存问题。

6. **HIGH — [test_skill_portability_lint.py:934](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:934)、`:995`：重复赋值整改仍未覆盖实际入口和赋值目标，合规常量仍可与最终值脱钩。**

   ```python
   P = "/tmp/cls-exam/x"
   P = "/var/cache/x"
   ```

   安全对照仅将第二行目标改为 `Q`。直接对两行调用 `_has_dynamic_tmp_join()` 返回 `True`，但正式入口先拆成两个单元，最终返回 `[]`。

   同单元也有未覆盖目标：

   ```python
   P = "/tmp/cls-exam/x"; P, = "/var/cache/x",
   ```

   解构赋值、属性赋值，以及不含 `/tmp` 常量的海象／增量覆写均能漏掉。另一个更简单的既存缺口是：

   ```python
   P = "/var/cache/x"  # "/tmp/cls-exam/x"
   ```

   合规串移入注释后仍贡献计数，实际赋值已改变，组合判据全部静默。

**MEDIUM：**

- **[test_skill_portability_lint.py:1662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1662)：`unset -f` 排除条件越过命令边界，新增漏检。**

  ```sh
  unset CLS_BACKEND_URL && curl -f "${CLS_BACKEND_URL:-http://localhost:8011}/x"
  ```

  `curl` 的 `-f` 被当作 `unset -f`，URL 检查返回 `[]`；`unset CLS_BACKEND_URL # -f` 同样漏掉。反方向，`unset CLS_BACKEND_URL_EXTRA` 和 `unset OTHER && curl "${CLS_BACKEND_URL:-…}"` 会误报。它们超出了已声明的“引号拼接变量名”残余。

- **[test_skill_portability_lint.py:1462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1462)：URL 放行计数没有绑定约定变量。**

  将 `${CLS_BACKEND_URL:-http://localhost:8011}` 改成 `${OTHER:-http://localhost:8011}`，九计数及全部附加判据不变。用户只配置约定变量时，命令会忽略它并回落到本机端口。

- **[test_skill_portability_lint.py:1096](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1096)、`:1722`：多行 opaque 记录只绑定首行，登记后仍有内容盲槽。**

  ```sh
  cp "/tmp/cls-exam/"\
  `printf a` out
  ```

  若登记此安全续行组，再仅把第二行换成 `` `printf .`./x out ``，实际路径变为 `/tmp/x`，但计数、全部集合和指纹 **`2:b9b2b0e5`** 都不变。此项需要已有登记额度，**不是对当前空额度的无条件绕过**。

**LOW：**

- **[test_skill_portability_lint.py:2821](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2821)、`:3098`：NBSP 样本没有承重所声称的空白修复。** 内存恢复 `_is_span_sep = isspace` 后，该断言仍通过，因为新增“引号数大于 2”分支代为报红；安全对照同时移除了前缀、相邻引号、NBSP 和命令替换。

- **[test_skill_portability_lint.py:1976](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1976)：补回的指纹测试没有检查正式消费端。** 内存让 `check_opaque_tmp()` 仅比较行号、忽略摘要后，该新增测试仍通过；它只证明摘要函数会变化，没有证明门使用了摘要。

其余指定维度逐项结论：

| 维度 | 复核结果 |
|---|---|
| 当前 `chunk + line + pad + pass` 探针 | **已删除**；函数说明仍描述旧实现。当前风险见 HIGH-1。 |
| 多行／单行 suite `elif`、普通 `if/else`、反斜杠续行、装饰器、异步语句、`match/case`、`except*` | **未发现所测有效语法的额外漏检。** heredoc 标记及普通 `case` 变量的问题见 HIGH-1。 |
| `With/withitem/comprehension/keyword/Starred/NamedExpr`、默认参数 | **未发现常量上溯节点层的额外漏放。** 不含 `/tmp` 的后续覆写是 HIGH-6 的另一层问题。 |
| 未闭合三引号／括号一直尝试到块尾 | 三引号可以一直返回 incomplete；但失败后会逐行回退，**未发现因此直接吞成单元、丢弃所有后续候选**。重复解析成本仍存在。 |
| fence 内 `- ` 行触发散文边界 | **未发现。** 普通 fence 的 body 与 `_prose_segments()` 确实分开处理。 |
| 交替列表／引用、`10.`、marker 后 tab、引用深度不一致 | **LOW，既存边界问题**：`:554–570` 的 depth 实际只是开关；`_strip_quote_prefix('> > P=1', 1)` 返回 `P=1`，会过剥。少一层引用时也不终止容器；tab 列问题见 HIGH-4。 |
| `_backtick_spans()` opening 掩码、原串 closing、等长 run | **未发现额外漏提。** 对非 ASCII 标点的过掩本身未导致额外反引号消失。 |
| span 与 CommonMark 内容归一化 | **LOW，既存误报**：`:331` 保留首尾空格，`` ` /tmp/cls-exam/x ` `` 会被报成越界候选。 |
| 空行、表格、HTML | 空行处理**未发现问题**；HTML 有 HIGH-5 的具体漏例，表格没有专门块处理，不能据此宣称完整遵循 Markdown 块语义。 |
| `_SPAN_SEP_CHARS` | 当前集合为空，**未发现枚举漏项造成漏检**；中文句读偏向误报。Unicode 分词问题见 HIGH-2。 |
| 缓存纯度、返回值隔离 | **未发现问题。** 未见外部状态依赖；修改一次返回列表不会污染缓存。 |
| `strip()` 摘要 | **未发现仅改首尾空白即可穿过当前登记项的独立反例**；已确认的多行绑定缺口见 MEDIUM。 |
| 形态表与两处内存变异 | 当前 **51 行**均满足指名判据坏红、安全绿，但 NBSP 行归因不承重。删除 closing 同字符条件、恢复分号截断，均使相应断言失败，**这两处未发现承重问题**。耗时测试已清缓存；未运行对树耗时测试。 |

`fence:`／`prose:` **确实会随格式调整翻转**。例如同一 `P="/tmp/x"` 从 fenced code 改成四空格缩进代码，提取结果可由两条 `fence:/tmp/x` 变成一条 `prose:/tmp/x`。这是候选来源与提取次数变化，不能当成物理债数量变化；`:1586` 的错误消息已有说明。U5-B 仍需同步九计数、来源多重集和受影响的登记项；U6 独立 scripts 不经过此提取器，**未发现新的交接影响**。

残余风险尚未完整声明：本轮仍有确定的新回归、既存静态漏检及登记后的内容盲槽，不能认定只剩保守误报和运行期不确定性。

**本轮 BLOCKER 0 条，HIGH 6 条。**
