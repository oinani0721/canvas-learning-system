复核绑定 **`0dbd2195f701b6bbe743b59ad9dd80fc8be7fcbe`**；收尾时测试文件 blob 与提交一致：`e10710c4cd2fb4a2e7359e42969674986a08f49e`。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。CommonMark 对照使用已安装的 `markdown_it`，只解析内存样本。

**最重要的问题：多重集差的计数思路正确，但当前实现把“没有新增候选”误当成“长单元可以丢弃”，引入了完整漏检。**

以下行号均指 [backend/tests/skills/test_skill_portability_lint.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py)。

**BLOCKER：未发现。**

**HIGH：4 条。**

1. **HIGH — [test_skill_portability_lint.py:848](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:848)：空 delta 丢掉长单元源码，却仍跳过其覆盖行，是本轮新回归。**

   在 Python fence 中：

   ```python
   if False:
       pass
   else:
       P = b"/t" b"mp/cls-exam/" + b"." * 2 + b"/x"
   ```

   安全对照只把 `b"."` 改成 `b"a"`。坏形态静态得到 `b"/tmp/cls-exam/../x"`。

   `_py_strings()` 不收 bytes，因此长短候选都是 `[]`；`if delta:` 不保存长单元，随后 `cur_j` 却前进。实测：

   ```text
   _parse_units → [(0, 'if False:\n    pass', [])]
   _has_dynamic_tmp_join(完整源码) → True
   dynamic_tmp_join_lines → []
   ```

   **两侧九计数全零，五项路径判据、URL 判据、块指纹全部为空。** 内存仅取消 `if delta:`、保留空候选长单元后，动态判据立即报红。这里没有跨块数据流。

2. **HIGH — [test_skill_portability_lint.py:1071](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1071)，关联 `:685`：纯 bytes 常量被交给一个不接收 bytes 的越界判据，属于既存未声明漏检。**

   ```python
   # 安全
   P = b"/t" b"mp/cls-exam/" b"a" b"./x"

   # 坏形态，仅改一个字符
   P = b"/t" b"mp/cls-exam/" b"." b"./x"
   ```

   AST 已将坏形态合成 `b"/tmp/cls-exam/../x"`，但 `_py_strings()` 返回 `[]`；动态判据抵达 `Assign` 后直接放行。

   **九计数、五项路径判据、URL、块指纹全部相同且为空。** 去掉 `b` 前缀后，相同字符串形态立即被越界判据抓到。这条不依赖 HIGH-1 的续接问题。

3. **HIGH — [test_skill_portability_lint.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:283)：fence opening 没有段落上下文，把不能打断段落的 `2. ~~~` 当成新围栏，连兜底网一起切断。**

   安全输入：

   ```text
   执行 `/tmp/cls-exam/a
   2. ~~~
   b/aa/aa/x`
   ```

   只把末行改成 `b/../../../x` 加结束反引号，就是坏形态。

   CommonMark 将三行解析为**一个 code span**；安全路径仍在命名空间内，坏路径规范化为 `/x`。本模块却从第二行开启 fence，丢失跨行 span。

   **九计数相同，其余语义判据全空，块指纹两侧都是 `S1:cda5bc06d70e9c56`。** 这是合法 Markdown 的完整静默面。

4. **HIGH — [test_skill_portability_lint.py:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:423)，关联 `:1884`：列表容器退出被误当成旧 fence 的 closing，没有重新处理该行，实际分块变化而全部指纹不变。**

   原输入：

   ```text
   - ~~~python
     pass
     ~~~
   P = "/tmp/cls-exam/" "." "./x"
   ~~~
   ```

   **只删除第三行的两个空格。**

   CommonMark 的结果从“第四行是散文”变成“第三行开启新的顶层 fence，第四行是合法的越界 Python 赋值”。本模块两侧都把第三行消费为旧 fence 的 closing，第四行仍归散文。

   **九计数相同，五项路径判据及 URL 全空，块指纹均为 `S4:20caea08b8c006a2`。** 这直接回答了“块划分变了但指纹集合不变”：存在。

**MEDIUM：6 条。**

1. **MEDIUM — [test_skill_portability_lint.py:676](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:676)：嵌套常量 `+` 链仍重复贡献子表达式，登记后可以抵消新增实际路径。**

   ```python
   # 一处实际 /tmp 值，却贡献两个候选
   P = "/t" + "mp" + ""

   # 两处实际 /tmp 值
   P = "/t" + "mp"; Q = "/t" + "mp"
   ```

   两侧越界结果完全相同：

   ```text
   [('/tmp', 'fence:/tmp'), ('/tmp', 'fence:/tmp')]
   ```

   九计数全零，其他判据及块指纹全空。**长短 Counter 差修好了窗口重叠，没有修好候选源头的重复贡献。** 此条需要先登记原形态，故列 MEDIUM。

2. **MEDIUM — [test_skill_portability_lint.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:403)，关联 `:291`、`:537`：第五版 fence 额度仍有双向错误。**

   下表中的 `\t` 表示真实 tab：

   | Opening／closing | CommonMark | 本模块 |
   |---|---|---|
   | `>\t~~~py`／`>\t  ~~~` | 不闭合 | 错误闭合 |
   | `> ~~~py`／`>    ~~~` | 闭合 | 不闭合 |
   | `-   ~~~py`／六空格加 `~~~` | 闭合 | 不闭合 |

   第一例把 tab 展开的全部列宽当成引用标记额度；第二例 closing 正则容不下“标记后一空格＋三空格内容缩进”；第三例列表内容基线实际为四列，却只计了 `- ` 两列。**引用标记和列表标记不能统一按“只取一个分隔字符”计算。**

3. **MEDIUM — [test_skill_portability_lint.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:623)：容器剥离没有深度上限，会把代码里的比较运算符也剥掉。**

   ```text
   > ~~~python
   > P = (
   >     "/tmp/cls-exam/"
   >     > "/etc/passwd"
   > )
   > ~~~
   ```

   CommonMark 保留代码中的第二个 `>`；本模块将它删除，把比较表达式变成隐式字符串拼接，动态判据由应报红变成 `[]`。**这类块内修改仍会被原文指纹接住，没有另计 HIGH。**

4. **MEDIUM — [test_skill_portability_lint.py:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:526)：散文段边界仍缺少上下文，存在多提和少提 span 两个方向。**

   - `执行 ` 加未闭合 span、下一行 `--`、再下一行路径：CommonMark 已形成 setext 标题，本模块仍跨标题拼出假 span。
   - 第一项为 ``- `未闭合``，下一项以 ``2. `/var/cache(`` 开始、路径在下一行闭合：CommonMark 有合法路径 span，本模块让前项夺走其 opening，返回越界结果 `[]`。

   当前段指纹会覆盖这些样本的内容变化，因此这是语义判据缺陷，未证明新的整门静默。

5. **MEDIUM — [test_skill_portability_lint.py:1821](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1821)：变量出现在同一个 shell 词内，仍不代表它控制服务地址。**

   ```sh
   # 安全
   curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"

   # 配置变量只进入 fragment
   curl "${OTHER:-http://localhost:8011}/x#${CLS_BACKEND_URL}"
   ```

   后者的主机端口仍由 `OTHER`／固定缺省值决定。**九计数相同，五项路径判据、URL、块指纹全部 `[] → []`。** 这是未声明的完整静默面。

6. **MEDIUM — [test_skill_portability_lint.py:1825](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1825)：`env` 判定忽略展开顺序，注释剥离也没有覆盖全部分支。**

   ```sh
   env -i curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   外层 shell 已先展开 URL，`env -i` 不会撤销参数中的配置；当前却报覆盖配置。`env -u` 同类。与之不同，清环境后再由 `sh -c` 展开才可能架空配置。

   此外，正常 curl 后附加 `# env -i`、`# unset CLS_BACKEND_URL` 或 `# CLS_BACKEND_URL=`，三者仍被误报：相关分支继续检查原文。

**LOW：2 条。**

1. **LOW — [test_skill_portability_lint.py:2233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2233)，关联 `:3499`：本轮核心整改缺少承重断言。**

   分别在内存恢复重复计数、成功扩张一次即停止、40 行扫描上限，**51 条指名形态＋8 条兜底形态＋3 条局部测试＋16 条三判据形态，均仍通过，共 78 项**。这不能证明整套 pytest 会通过，但已证明这些现有纯断言没有锁住相应整改。

2. **LOW — [test_skill_portability_lint.py:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:331)：code span 未执行 CommonMark 的内容空白归一化，会把正常路径误报为越界。**

   ``执行 ` /tmp/cls-exam/x ` `` 的实际 code 内容是 `/tmp/cls-exam/x`，模块却把两侧空格也送入 `normpath`，产生 `prose: /tmp/cls-exam/x ` 候选。

其余维度的明确结论：

| 维度 | 复核结果 |
|---|---|
| `Counter(长)-Counter(短)` 算术 | **未发现算术漏检。** 短一次、长两次贡献一次；四个分支同值保留四次。问题在 HIGH-1 的源码保留条件及 MEDIUM-1 的候选来源。 |
| 中途 `grown is None` | **未发现已收 delta 丢失或未消费行被跳过。** `cur_j` 留在上次成功位置，剩余行继续回退解析。实现是用最新 `Counter(got)` 更新 `seen`。 |
| 40 行与长分支 | **未发现固定窗口残留。** 80 行体内语句后续接、80 行多行 `elif` 头均正常提取。 |
| 续接词／探针 | 当前是宽关键词触发，已没有题述冒号限制及 `pass` 探针。所测 `else \` 换行冒号、`except*`、装饰器、async、match/case、heredoc `else`：**未发现新的截断。** |
| 不完整输入吞块 | 所测未闭合括号最终回退，末行仍被处理，**未发现候选整块吞失**；不能据此证明任意输入成本有界。 |
| AST 节点边界 | 除 HIGH-2 的纯 bytes 外，所测 `With/withitem/comprehension/keyword/Starred/NamedExpr`、装饰器和默认参数，**未发现节点层误放**。 |
| 缓存 | **未发现外部状态依赖或返回值污染缓存。** 返回候选列表被修改后，下次读取不受影响。 |
| fence 内列表样式代码 | 普通 fence 内 `- ` 不进入散文段边界判断，**未发现这项假设失效**；容器过剥另见 MEDIUM-3。 |
| 原文切片索引 | **未发现嵌套容器导致 `start/len(body)` 错位。** 当前逐物理行一对一追加。 |
| 指纹稳定性 | 当前是 **sha16，且不 `strip()`**。内部行序、行尾空格变化会改变摘要；CRLF、文件末尾换行归一化稳定。末尾连续 CR/LF 被忽略；closing 行缺失的实际风险见 HIGH-4。 |
| backtick 转义扫描 | 除内容归一化问题，所测 opening 掩码／原串 closing／等长 run **未发现新的扫描漏检**；`\.` 多掩非标点没有在所测样本中造成反引号丢失。 |
| shell 手写分词 | 仍不是完整 shell 分词器；Unicode 空白、转义引号等已有形态仍依赖块指纹。不能认定 `$'…'`、反引号内空格等任意组合已完整覆盖。 |
| 来源前缀 | 格式调整会改变提取次数或 `fence/prose` 归属；当前报错已解释来源翻转，**未发现新的 Counter 诊断问题**。次数不能当物理债数量。 |
| 旧两处内存变异 | **未发现承重问题。** 删除 closing 同字符条件、恢复分号截断，对应断言均失败。 |
| 形态表 | 当前指名表实际 **51 行**，三判据表 **16 行**；所测坏形态命中指名判据，安全对照对该判据为绿。部分对照并非严格只差一处，不能外推为完整等计数证明。 |
| r13 的“8/9” | 允许文件中 `_NET_ONLY_FORMS` 实际只有 **8 条，独立确认 8/8**；无法核实历史第九例。另一张表确认 **45/51**，剩余六例被其他判据接住。 |
| handoff／scripts | 八条交接纯断言通过；所测脚本端口指标 **未发现问题**。没有执行会读取其他文件的覆盖外扫描，也没有重测禁读正文的当前基线。 |

**已声明的跨块边界确实很大，远不止特殊编码。** 第一块保持 `P = "/tmp/cls-exam/x"`，第二块把 `P.replace("cls-exam/", "cls-exam/")` 改为 `P.replace("cls-exam/", "")`，实际落点就变成 `/tmp/x`；九计数及全部附加判据仍相同，第一块指纹也不变。普通后续变量变换就能进入这条静默面。它属于你明确声明未修的限制，本轮不另计 HIGH。

残余风险尚未全部如实覆盖：除已声明跨块限制外，以上仍有可静态确定的漏检，不能收尾为只剩保守误报。

**本轮 BLOCKER 0 条，HIGH 4 条。**

