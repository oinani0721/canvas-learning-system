**兜底网尚未修到位，仍有完整静默漏检。**

复核绑定 `7245a67af6fe85a5ddbda71ac03338e7f6acbd91`；收尾时测试文件 blob 为 `aa5795ee46d9ea895c8dc3c043d7ab84f611a26a`，与该提交一致。仅使用指定读取面和内存样本，未运行 pytest、修改文件或连接网络／数据库。

以下“完整静默”均指：安全／坏形态的**九项计数、六项附加判据结果及块指纹全部相同**。

**BLOCKER：未发现。**

**HIGH：3 条。**

1. **HIGH — [test_skill_portability_lint.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:381)、`:402`：本轮恢复 `open_indent + 3`，重新引入提前闭合回归；引用前缀后的 tab 缩进也仍未正确计算。**

   精确坏形态，opening 前三个空格，中间标记前四个空格：

   ````text
      ```python
   P = "/tmp/cls-exam/x"
   TEXT = '''
       ```
   '''
   Q = ("/tmp/cls-exam/"
        + "." * 2 + "/x")
      ```
   ````

   安全对照只把 `* 2` 改成 `* 0`。本地 CommonMark 解析确认：中间四空格标记是内容，整块是合法 Python；`Q` 从命名空间内变成 `/tmp/x`。

   本模块却在第 4 行提前闭合，把后半段当散文。两者六项附加结果全部为空，指纹同为：

   ```text
   B2:2118ddd9581d9028
   L6:3a457d557a8b622c
   ```

   **同根 tab 反例也成立**：opening 为 `> ```python`，中间标记为 `>`＋两个真实 tab＋三个反引号。引用内容实际仍有超过三列的缩进，但 `_indent_cols()` 只数 `>` 前面的缩进，得到零，仍然提前闭合。合并计一条 HIGH。

2. **HIGH — [test_skill_portability_lint.py:548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:548)、`:1789`：标题后的段边界缺失，配合散文只绑定含 `/tmp` 的物理行，使同一个跨行 code span 内的越界修改完全静默。**

   ```text
   # 标题 `未闭合
   执行 `P = ("/tmp/cls-exam/"
   "../x")`
   ```

   安全对照只把第三行 `"../x"` 改成 `"a/x"`。

   CommonMark 将标题单独成块，后两行产生：

   ```python
   P = ("/tmp/cls-exam/" "../x")
   ```

   AST 确认这是常量拼接，规范化结果为 `/tmp/x`。本模块只在标题**前**断段，标题里的未闭反引号夺走后段 opening；第三行又不含 `/tmp`，未进入指纹。

   **完整静默**，指纹均为 `L2:b8f816f8e166d41f`。这是同一个 span 内的静态漏检，不能归入跨块变量分析边界。

3. **HIGH — [test_skill_portability_lint.py:713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:713)、`:778`、`:785`：无关续接词会使已成功的 Python 解析被丢弃，随后降级分词丢失常量拼接。**

   合法 shell heredoc：

   ```sh
   python3 - <<'else'
   P = "/t" "mp/cls-exam/../x"; print(P)
   else
   ```

   放入普通 fence，安全对照只把 `cls-exam/../x` 改成 `cls-exam/x`。

   heredoc 结束标记 `else` 被误当作 Python 续接；累加失败后转交 shlex，将相邻字符串拆开。**九项计数全零，六项附加结果和指纹全部为空**。把结束标记换成 `PY`，越界判据立即正确检出 `fence:/tmp/x`。

   `elif`、`except`、`finally` 作为结束标记同样复现。这只需要单条语句的常量折叠，不需要跨块数据流。

**MEDIUM：4 条。**

1. **MEDIUM — [test_skill_portability_lint.py:1730](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1730)：词边界仍只证明名字出现在行内，不能证明 URL 使用了它。**

   ```sh
   # 安全
   curl "${CLS_BACKEND_URL:-http://localhost:8011}/health" # CLS_BACKEND_URL
   # 坏形态
   curl "${OTHER:-http://localhost:8011}/health" # CLS_BACKEND_URL
   ```

   包进 fence 后完整静默；坏形态中用户配置 `CLS_BACKEND_URL` 不生效。名字子串问题缩小了，但绑定问题未解决。

2. **MEDIUM — [test_skill_portability_lint.py:888](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:888)、`:1748`：URL 改走逻辑行后，仍被六次续接上限截断。**

   用 `'unset -v ' + ('\\\n' * 7) + 'CLS_BACKEND_URL'` 构造命令，后接正常 curl；安全对照仅将 unset 目标改成 `OTHER`。**六次续接能检出，七次、八次完整静默**，实际却会清空配置。

3. **MEDIUM — [test_skill_portability_lint.py:1778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1778)、`:1784`：围栏语言标记未绑定，改变解释器可改变路径语义而不改变任何基线结果。**

   ````text
   ```sh
   P="/tmp/cls-exam/"'\x2e\x2e/x'
   ```
   ````

   仅将 `sh` 改成 `python`：shell 保留单引号中的反斜杠，路径仍在命名空间内；Python 得到 `/tmp/cls-exam/../x`。全部结果相同，包括原有的越界／opaque 登记项，指纹同为 `B2:f8b28664aec0c1b9`。此问题以执行者按语言标记选择解释器为前提。

4. **MEDIUM — [test_skill_portability_lint.py:355](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:355)、`:1775`：`splitlines()` 会把具有 shell 语义的控制字符当换行，原文指纹仍存在规范化静默面。**

   fence 内安全输入为：

   ```text
   P="/tmp/cls-exam/"<VT>P="/etc/passwd"
   ```

   `<VT>` 表示真实 U+000B。只将它改成 LF：前者是一个赋值，路径仍在命名空间内；后者成为两个赋值，最终值为 `/etc/passwd`。shlex 验证前者是一个词，但本模块对两者产生完全相同的分块和结果，指纹均为 `B2:c9069546a6453145`。考虑输入较冷门，列 MEDIUM。

**LOW：1 条。**

- **LOW — [test_skill_portability_lint.py:2199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2199)：NBSP 样本整改仍未完成。**

  `_NET_ONLY_FORMS` 中“NBSP 分隔的两段引号”仍使用 ASCII 空格，实测 `'\u00a0' in bad` 为 `False`。本轮修改的是另一张表的说明，尚不能据此声称该负控验证了 NBSP。

**其余问题逐项结论：**

| 维度 | 独立复核结果 |
|---|---|
| `start` 与原文切片映射 | **未发现错位。** 每处理一行恰追加一个 body 元素，容器剥离不改变数量；但共同依赖的 `splitlines()` 有上述 MEDIUM。 |
| 行序、行首／行尾空格、body 容器前缀 | **未发现指纹静默。** 当前为 sha16，保留这些变化。 |
| CRLF、LF、文件末尾换行 | **未发现不稳定。** 实测指纹一致。 |
| 块末尾纯空行 | 会被 `rstrip("\r\n")` 忽略，块长度不同也可同指纹；**未发现仅此引入实际债**的反例。 |
| fence 内以 `- ` 开头的代码 | **未发现被散文边界截断。** 散文分段跳过整个 fence。 |
| 交替列表／引用、多字符 marker、深度不一致 | 剥离仍不精确：`depth` 实际仅作开关，会持续剥前缀；原文绑定通常接住内容变化，**未发现额外完整静默**。closing 的 tab 问题见 HIGH-1。 |
| 续接探针 | 当前已删除，问题中的 `ast.parse(... + "pass")` 不再适用；剩余吞并问题见 HIGH-3。 |
| `case = 0` | **未发现残留。** 200 行实测形成 200 个单元。 |
| `With/withitem`、comprehension、keyword、Starred、NamedExpr、装饰器、默认参数、`except*`、多行 `elif` | 所测有效语句均触发预期判据，**未发现新的节点层漏放**。 |
| 缓存纯度与返回值隔离 | **未发现问题。** 未发现外部状态读取，修改返回列表不污染缓存。 |
| 无行数上限、`codeop` | 平方级累加成本仍存在；**未发现额外有效 Python 终止缺口**，主要静默反例是 HIGH-3。 |
| 手写 shell 分词 | 转义引号、未闭引号、ANSI-C 引号、反引号内空格仍不等价于 shell；`\s` 也会误切 NBSP。所测普通替换由指纹接住，**未发现额外完整静默**。 |
| backtick 掩码、原串 closing、等长 run | **未发现新的扫描器缺陷**；实际段边界漏检见 HIGH-2。 |
| 空行、setext、根列表项 | 所测分段正常，**未发现新问题**；HTML／引用块仍非完整 CommonMark 解析。 |
| `_SPAN_SEP_CHARS` | 当前为空，仅认空格／tab；中文标点会带来保守误报，**未发现新的放行面**。 |
| `fence:`／`prose:` 来源翻转 | 格式调整确实可能报红；`:1632` 已说明它是提取来源，**未发现新增误导**。U5-B 仍需同步受影响的附加基线，不能只改九计数。 |
| U6 交接常量 | `check_handoff_constants()` 返回 `[]`，**未发现本轮问题**。未评宿主可跑性。 |

**断言与数字：**

- `_NET_ONLY_FORMS`：**8/8** 指纹区分。
- `_R7_HIGH_FORMS`：**51/51** 指名判据坏红／安全绿。
- 指纹：**45/51**；未区分六例确为**四 URL＋两 Python 拼接**，均有其他判据接住。
- **r13 的 8/9 无法完整复核**：获准材料没有完整九例，不能拿当前 8/8 替代。
- 三判据表当前实际为 **16 行**，直接调用全部通过。部分安全对照改变了结构或行数，并非严格只差一个局部。
- 将 `check_tmp_blocks()`、`check_opaque_tmp()` 在内存改成恒返 `[]`，当前消费端断言均失败，**承重**。
- 删除闭合同字符限制、恢复候选分号截断，两种旧变异也被对应断言抓住。
- 指名判据已经坏红后，再断言“至少一个判据红”，**没有额外承重**。

已声明的“不含 `/tmp`”边界**远大于少数特殊编码**：普通跨块变量覆盖、同一 fence 内拆写字面量后的后续赋值，以及“上一行声明目录、下一行改成写父目录”的散文，都能完整静默。除此之外，上述 HIGH 还包含不需要跨块分析的静态漏检，因此残余风险尚未完整声明。

**本轮 BLOCKER 0 条，HIGH 3 条。**
