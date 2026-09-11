复核绑定 **`7dcf96f2270f2dd5758a0859c7421b843ab160e9`**；测试文件 blob 为 `05d240db52dfab3cdad34ed70b7f5e8c5750ccfd`，收尾确认工作区文件与提交一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：1 条，合并两个同根反例。**

1. **HIGH — [test_skill_portability_lint.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:399)、[`:404`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:404)、[`:1759`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1759)：第十条对错误分块、剥过前缀的内容取指纹，真实代码块发生语义变化仍可完全静默。**

   **反例 A：tab 导致提前闭合。** 以下第四行以一个真实 tab 开头：

   ````text
   ```python
   P = "/tmp/cls-exam/x"
   S = '''
   	```
   '''
   Q = "/var/cache/x"
   ```
   ````

   仅把第六行 `Q` 改为 `P`。本地 CommonMark 解析确认整个内容仍是一个围栏，且是合法 Python；内存执行确认最终 `P` 从 `/tmp/cls-exam/x` 变成 `/var/cache/x`。

   当前实现把 tab 按一个字符计缩进，在第四行提前闭合，后半段不进块指纹。两边**九项计数相同、六项附加结果全部为空，指纹均为 `B2:bb56528a`**。

   **反例 B：真实块划分改变，指纹集合不变。**

   ````text
   > ```python
   > P = "/tmp/cls-exam/x"
   P = "/var/cache/x"
   > ```
   ````

   仅给第三行加 `> `。CommonMark 下，原第三行在代码块外；修改后进入代码块并覆盖 `P`。当前实现没有在退出引用容器时终止围栏，又剥掉新增前缀，两边 `_fence_blocks()` 输出完全相同，六项附加结果均为空，指纹均为 **`B2:45dad0ef`**。

   因此，第十条目前没有兑现“含 `/tmp` 的真实块改了就红”。

**MEDIUM：4 条。**

1. **MEDIUM — [test_skill_portability_lint.py:1822](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1822)：`strip()` 会删除具有 shell 语义的尾随空格，已登记的保守项可被静默改成真实越界。**

   安全行是 `执行 P="/tmp/cls-exam/.."\␠`，其中 `␠` 表示一个真实空格；坏形态仅删除最后这个空格。

   只执行赋值与输出的 shell 验证结果：

   - 安全值：`/tmp/cls-exam/.. `，末段是带空格的目录名。
   - 坏值：反斜杠续行至空行后得到 `/tmp/cls-exam/..`，规范化为 `/tmp`。

   两边完整签名相同：越界均为 `prose:/tmp`、可疑行均为 `[1]`，opaque 与新网摘要均为 `7c435e62`。**安全形态的保守记录一经登记，删除空格便不会报红。**

2. **MEDIUM — [test_skill_portability_lint.py:377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:377)：本轮减去 `_lead` 会错删列表容器自身的整体缩进，新增错误不闭合。**

   opening 为三空格后接 `- ```python`，body 缩进五空格，closing 缩进六空格时，CommonMark 正常闭合；新版阈值却只有五，吞入后续散文。三空格后接 `10.`、closing 缩进八空格同样成立。

   内存恢复旧表达式 `_open_m.start(1)` 后恢复正确分块，确认是本轮回归；此例主要造成误吞、成本及误报。

3. **MEDIUM — [test_skill_portability_lint.py:1713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1713)：URL 放行仍只绑定名字子串，未绑定实际展开变量。**

   将 `${CLS_BACKEND_URL:-http://localhost:8011}` 仅改成 `${CLS_BACKEND_URL_OTHER:-http://localhost:8011}`，用户配置的约定变量便不再生效，但九计数相同，六项附加结果与新网全部为空。`${OTHER:-…}` 配上 `# CLS_BACKEND_URL` 注释也能通过。

4. **MEDIUM — [test_skill_portability_lint.py:1732](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1732)：URL 检查按物理行执行，漏掉合法的 `unset` 续行。**

   安全形态：

   ```sh
   unset -f \
   CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api"
   ```

   仅将 `-f` 改为 `-v`，就从删除函数变为清空环境变量；两边行数、九计数、六项附加结果及新网仍全部相同。这不是已声明的“变量名引号拼接”边界。

**LOW：5 条。**

1. **LOW — [test_skill_portability_lint.py:2156](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2156)、[`:2208`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2208)：新网负控没有验证正式消费端。** 内存将 `check_tmp_blocks()` 改成恒返 `[]` 后，正控、八组新样本、45/51 断言及基线键完整性检查仍全部通过；摘要函数承重，正式门失效没有被负控抓住。

2. **LOW — [test_skill_portability_lint.py:1822](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1822)：sha8 只有 32 位，已构造出安全／坏内容的实际碰撞。** 以下块体：

   ```python
   P = "/tmp/cls-exam/x"
   Q = "/var/cache/x"  # 133530
   ```

   将第二行替换为 `P = "/var/cache/x"  # 19218`，两边摘要均为 **`50014ee0`**，完整正文判据签名也相同。此证据需要选择两边样本，**不代表已经撞中现有十二项固定基线**，因此不计 HIGH。

3. **LOW — [test_skill_portability_lint.py:2170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2170)：标为 NBSP 的样本实际使用 ASCII 空格 U+0020。** 当前断言不能证明原 NBSP 反例得到覆盖。

4. **LOW — [test_skill_portability_lint.py:2226](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2226)：45/51 数字成立，但“余六例全归 URL/unset”的归因没有被断言验证，而且事实不符。** 实际是 **四例 URL、两例 Python `/t` 与 `mp` 拼接**；后两例由动态拼接判据检出。

5. **LOW — [test_skill_portability_lint.py:702](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:702)：独立的 `case = 0` 被软关键字正则当成续接，错误合并无关语句。** 200 行被合成一个单元，实测约 0.072 秒；同量 `x = 0` 为 200 个单元，约 0.0016 秒。这里证明的是错误合并和成本退化，未据此发现新的整体漏检。

**8/9 与断言承重的独立结果：**

| 项目 | 结果 |
|---|---|
| `_NET_ONLY_FORMS` 八组 | **8/8 可由新网区分**；九计数相同，六项语义输出双方全空 |
| 题干第九类 `${OTHER:-…:8011}` | 新网无法区分；当前 URL 判据能够检出 |
| 原 r13 九例逐字复跑 | **未确认**；允许读取面没有原 r13 报告，且 NBSP 样本存在上述替换 |
| 当前指名形态表 | **51/51 通过**，未发现指名判据选错；部分安全对照仍不满足“结构相同、只差一处” |
| 另一张三判据表 | 当前为 **16 行，16/16 通过** |
| 删除 closing 同字符条件 | 原断言失败，**未发现承重问题** |
| 恢复分号截断 | 分号载体的越界断言失败，**未发现承重问题** |

**其余指定维度：**

| 维度 | 复核结果 |
|---|---|
| 块内行序交换 | 不同内容行交换会改变指纹；排除碰撞后，**未发现顺序丢失** |
| 行尾空白、CRLF | 内部行尾空白通常改变块指纹；整个块末尾及散文行两端空白被 `strip()` 删除；LF/CRLF 经 `splitlines()` 后指纹相同 |
| `_shell_words()` | 转义引号、未闭合引号、NBSP、反引号内空格仍不符合真实 shell 分词；`$'…'` 也未解析其转义语义。一般含 `/tmp` 的文本变动由新网检出，例外见上述发现 |
| 普通 fence 内 `- ``` ` | **未发现错误闭合**；非零容器深度下过度剥前缀属于 HIGH-1 |
| 续接探针 | 当前实现已经没有 `chunk + line + pad + pass` 探针，仅旧说明残留；该问题前提不适用于最终 HEAD |
| `codeop`、分支和异步语句 | 验证的合法多行 `elif`、`except*`、`match/case`、`async def` 保留完整单元；**未发现这些形态的新漏检** |
| 无行数上限 | `_py_needs_more()` 并非唯一终止条件，`follows` 可覆盖其判断；确有一直尝试到块尾再回退的成本面，见 LOW-5 |
| AST 常量归属 | `With/withitem/comprehension/keyword/Starred/NamedExpr`、装饰器及默认参数均触发动态判据；**未发现节点层新误放** |
| 缓存纯度 | 正常调用不读外部文件或服务；修改返回列表不会污染缓存，**未发现缓存污染** |
| 散文段边界 | 当前已识别空行和列表项，并非只认 fence；HTML、标题等仍不是完整 Markdown 分块，存在错误 span，不能宣称解析完整 |
| backtick 扫描与转义掩码 | 本次反斜杠、非 ASCII 转义对照中，**未发现 opening/closing 掩码导致的新丢 span**；首尾单空格未按 CommonMark 规范化，仍可保守误报 |
| 中文分隔符 | `_SPAN_SEP_CHARS` 当前为空，只认 ASCII 空格/tab；中文标点紧贴 span 的误报属于已登记取舍，**未发现新增白名单漏放** |
| `fence:`／`prose:` 与交接 | 格式变化仍可能翻转来源；正式诊断已解释来源不等于物理债数，**未发现新的诊断缺陷**。U5-B 需同步受影响的附加基线和新网，不能只改计数段；U6 常量检查及八组交接正反例通过 |

**不含 `/tmp` 的已声明边界，实际比跨块变量更大。** 同一个 Python 块中保持 `T = "/t" + "mp/cls-exam/"`，把下一行 `P = T + "a/x"` 改为 `P = T + "../x"`，九计数全零，六项附加结果与新网全空。即使第一块直接写明 `/tmp` 并被指纹固定，第二块修改其用途仍可静默；散文中只修改下一行的“这个目录的上一级目录”也一样。故这不是少数特殊编码，而是未包含原文字面量的使用处和上下文整体不受新网保护。

残余风险尚未全部如实声明：分块导致覆盖丢失、语义空白被删除，以及 URL 的两条确定性漏检仍在；目前不能认定只剩已接受边界和保守误报。

**本轮 BLOCKER 0 条，HIGH 1 条。**
