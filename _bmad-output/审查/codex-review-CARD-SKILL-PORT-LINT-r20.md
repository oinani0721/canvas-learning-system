本轮仍有未闭环缺陷。复核绑定 **`8c34481a94a7d156b1bc3f2e3760a1e9a835c09d`**，收尾时被审文件与提交一致。全程只读，未跑 pytest、读取禁读正文或连接服务。

以下均指 `backend/tests/skills/test_skill_portability_lint.py`；重复问题按根因合并。

**BLOCKER：未发现。**

**HIGH：2 条。**

1. **HIGH — [test_skill_portability_lint.py:1068](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1068)：整段预筛修通了，但重复赋值检查仍漏掉显式折叠的 `/tmp`。**

   同一个合法 Python 单元：

   ```python
   P = "/t" + "mp/cls-exam/x"; Q = "/etc/passwd"
   ```

   只把 `Q` 改成 `P`，实际最终路径变为 `/etc/passwd`。实测两版**九项计数全部为零，七组附加结果全部为空**，包括块指纹。

   原因是 `tmp_targets` 仍只检查叶常量是否包含 `/tmp`，没有使用折叠后的值。`:1127` 的新预筛已经放行，但消费端仍返回 False。bytes 同形态也漏，合并计一条。这是**既存未声明缺口，相关整改尚未贯通**。

2. **HIGH — [test_skill_portability_lint.py:425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:425)、`:1906`：列表退出仍被当作 closing，closing 又未纳入指纹。已知未修，归你决定另立的分块卡。**

   ````text
   - ~~~py
     T = "/tmp/cls-exam/x"
     ~~~
   P = "/etc/passwd"
   ~~~
   ````

   **只删第三行两个空格**，本地 CommonMark 对照中第四行从散文进入新 fence；模块两版九计数相同，六项语义结果均为空，指纹均为：

   ```text
   B2:0409134db7c0384a
   ```

   因此，**另立分块卡的处置正确；这是随手修改即可触发的风险**。单层列表已经足够，无需嵌套、setext 或 HTML。关于九份正文的现有写法，本轮采用你给定的前提，没有重新读取。

**MEDIUM：5 条。**

1. **MEDIUM，新回归 — [test_skill_portability_lint.py:1836](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1836)：注释剥离不识别引号和参数展开，会吞掉真实命令。**

   ```sh
   printf "#"; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   被截成 `printf "`，后面的 `unset` 漏检。安全对照仅把 `unset` 换成 `:`，**全部计数、附加判据和指纹相同**。`${#CLS_BACKEND_URL}` 的长度展开也会触发同样错误；赋值分支同样受影响。

2. **MEDIUM，整改未到位 — [test_skill_portability_lint.py:1845](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1845)：截掉 query/fragment，并不等于只检查主机和端口。**

   ```sh
   curl "${OTHER:-http://localhost:8011}/${CLS_BACKEND_URL}"
   ```

   变量只出现在 path，主机端口仍由 `OTHER` 决定，但判据放行。与正常缺省 URL 相比，**全部指标和指纹相等**。

3. **MEDIUM — [test_skill_portability_lint.py:1854](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1854)：`env` 判定仍有双向缺陷。**

   - `env --ignore-environment bash -c '…'`、`env -uCLS_BACKEND_URL bash -c '…'` 清除环境后展开缺省 URL，均漏检。
   - `env -i bash -c 'true'; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"` 却误报：清环境的是无关子进程。
   - 双引号包裹 `-c` 脚本、使 URL 已在外层展开的形态，也仍可能误报。

   前两种漏检均已验证安全／坏形态全门等值；新增 bash 支持也扩大了后两种误报面。

4. **MEDIUM，新扩展的身份损失 — [test_skill_portability_lint.py:666](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:666)：`decode(..., "replace")` 确实会把不同 bytes 路径折成同一候选。**

   ```python
   P = b"/t" + b"mp/\xff/x"
   ```

   把 `\xff` 换成 `\xfe`，两者都得到 `fence:/tmp/�/x`；九计数、越界多重集及其余判据全部相同。**一旦登记这种候选，另一条不同 bytes 路径可以静默替换它。**

   另外，逐叶解码使 `b"\xc3" + b"\xa9"` 得到 `��`，完整 bytes 解码却是 `é`。但**未发现 U+FFFD 把命名空间外路径误判为命名空间内路径**，不能把这个问题夸大成合规→越界的假绿。

5. **MEDIUM，既存误报 — [test_skill_portability_lint.py:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:331)、`:954`：code span 未做 CommonMark 空白归一化。**

   `` ` /tmp/cls-exam/x ` `` 渲染后的内容是合规路径，模块却报 `prose: /tmp/cls-exam/x `；跨行 span 的换行也没有转换为空格。

   **这条值得在本卡局部修复，不需要容器栈。** 它能减少常见写法的误报，但不是本轮已证明的全门静默缺口：修改这些空白时，块指纹会变化。若推迟，应单独登记“span 归一化”，不要归因为必须先实现容器栈。

**LOW：3 条。**

1. **LOW — [test_skill_portability_lint.py:709](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:709)、`:2357`：bytes 叶常量收集仍缺承重断言。**

   内存仅撤销这处收集，**94 次现有纯函数断言仍全部通过**，但下面的越界结果变成空：

   ```python
   P = b"/t" b"mp/cls-exam/" b".." b"/x"
   ```

   新断言锁住了显式 `+` 折叠，没有锁住隐式拼接后的 bytes `Constant` 收集。

2. **LOW — [test_skill_portability_lint.py:2357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2357)：本轮 URL 重写缺相应回归断言。**

   新增测试覆盖常量链、bytes、整段预筛；未覆盖本轮修改的注释、`env`、path/query 等分支。允许材料中可定位的 URL 指名形态为 **4 对，全部通过**，不能据此独立确认“9/9”。

3. **LOW — [test_skill_portability_lint.py:2420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2420)：现有性能哨兵测不到新增整段预筛成本。**

   它只测 `_parse_units()`，不调用包含 `:1127` 新增工作的动态判据。

预筛新增的不只是一次 `ast.parse`，还包括 `_py_strings()` 的 AST 遍历和递归折叠。隔离回退新增预筛、预热单元缓存后的合成 A/B 如下：

| 语料 | 修改前→当前 |
|---|---:|
| 现有形态表的 102 个安全／坏文本 | 1.708→3.473 ms，约 2.03 倍 |
| 1000 个普通赋值单元 | 0.264→9.420 ms |
| 1000 个明文 `/tmp` 赋值单元 | 12.978→21.926 ms |
| 60 个 `elif` 链 | 17.595→33.536 ms |

这些不是九份正文的实际耗时；受读取边界限制，**本轮无法给出当前树总增量**。

其余维度逐项结果如下：

| 维度 | 复核结果 |
|---|---|
| 长短单元差集、重叠次数、扩张失败 | **未发现问题。** 短单元一份路径、长单元两份相同路径，随后扩张失败，最终仍恰好两份；此前结果保留，未消费行继续处理。 |
| 40 行上限、占位 `pass` 探针、强制冒号规则 | 当前实现已经没有这些规则。`:729` 是宽续接词触发器，`:859` 可扩张到块末。不能再按旧实现评判。 |
| heredoc 结束标记与续接词歧义 | **未发现新的候选丢失。** 当前保留短单元，再尝试扩张；失败不会撤销短单元。 |
| AST 节点及合法 Python 续接 | **未发现新漏检。** 针对 With、keyword、Starred、NamedExpr、装饰器、默认参数、comprehension、async、`except*`、反斜杠续接的合成检查均触发预期判据。 |
| 不完整 Python 一直尝试到块尾 | **未发现随后语句因此永久丢失。** 失败后仍回退恢复；但最坏解析成本会增长，不能保证线性成本。 |
| 缓存纯性 | **未发现外部状态依赖或调用方污染缓存。** 内部存 tuple，返回时复制 list。 |
| `_shell_words()` | 边界仍在：转义引号会误切，未闭合引号可被跳过，`$'…'` 不按 Bash 解码，反引号内空格会被切开。不能视为完整 shell 解析；URL 已有上面的实际漏检。 |
| fence 内 `- ` 是否被散文分段切走 | 普通无容器 fence **未发现问题**；引用 fence 的前缀剥离仍可能把代码 `> - x` 剥成 `x`，属于分块卡。 |
| backtick opening 掩码、原串 closing、等长 run | **未发现新的扫描／转义回归。** 仍有上述空白归一化问题。 |
| `_SPAN_SEP_CHARS` | 当前为空，只放行 ASCII 空格/tab；旧问题中的中文标点白名单已不存在，**未发现该白名单造成的新漏检**。 |
| 原文切片的行号对应 | **未发现索引错位。** 每次循环消费、追加一个物理行；容器语义错误发生在分块和前缀剥离层。 |
| 指纹空白、行序、CRLF、末尾换行 | 当前是 SHA256 前16位、`rstrip("\r\n")`，不是旧版 strip/sha8。**未发现常规稳定性问题**：LF/CRLF等值，末尾无换行等值；行序、普通行尾空格变化会改摘要。 |
| 来源前缀和交接 | 格式调整确实可能使 `prose:`／`fence:` 翻转；`:1743` 已解释这是提取来源变化。**未发现新的来源归属说明缺口。** 交接常量纯函数返回 `[]`。 |
| 形态表与本轮三段断言 | 当前表为 **51 行**，不是旧提问中的15行。94次可安全调用的现有断言通过；分别回退最外层折叠限制、bytes折叠、whole预筛，均使新增测试失败。**三处承重未发现问题**；遗漏的是上面的 bytes 叶收集。 |

fence 的双向反例仍然存在，均归 HIGH-2 的分块根因：

| 输入 | CommonMark／模块差异 | 位置 |
|---|---|---|
| opening `-   ~~~py`，closing 缩进6格 | CommonMark闭合，模块不闭合 | `:403`、`:537` |
| opening `> ~~~py`，closing `>    ~~~` | CommonMark闭合，模块不闭合 | `:291` |
| opening `>\t~~~py`，closing `>\t  ~~~` | 模块提前闭合，CommonMark保留为内容 | `:403`、`:425` |

因此，“额度这次对了吗”的答案仍是**没有整体成立**；tab列宽、列表分隔空白和容器退出不能仅靠一个最大缩进阈值解决。

兜底网的边界也明显大于“少数特殊编码”。保持第一块 `P = "/tmp/cls-exam/x"` 不动，只把另一块中的 `Q = "/etc/passwd"` 改成 `P = "/etc/passwd"`，九计数和全部附加结果均不变，含 `/tmp` 的块指纹也不变。**普通直接赋值就能触发**，无需特殊编码。这属于你已声明的跨块边界，不重复计为新 HIGH。

关于“r13 的 8/9”：允许代码中的 `_NET_ONLY_FORMS` 是 **8项，实测8/8可区分**；主形态表是 **51项，45/51可由指纹区分**。没有获准材料中的第九个具体输入，不能独立确认历史“8/9”。

残余风险尚不能称为全部闭环：分块与跨块边界已经明确，但本轮仍发现折叠常量重复赋值漏检，以及 URL 新回归和未完成的整改。

**本轮 BLOCKER 0 条，HIGH 2 条，其中1条为本卡未闭环缺口，1条为已决定另立分块卡的既存问题。**
