复核绑定 **`cb35d97ebe380e351fe3504ff41e792da0e992fa`**；收尾时测试文件与提交 blob 一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**整体判断：六项登记缺陷不能归为“理论存在”。** 单层列表、单层引用就能触发；其中已经复现“只删两个空格，全部正文门仍静默”。原文指纹能接住多数正文修改，但没有消除容器边界的漏检。我建议另立 Markdown 分块卡。“九份不用嵌套、setext、HTML”不足以排除这些问题；这项当前树描述沿用你的前提，未越界重扫正文。

**BLOCKER：未发现。**

**HIGH：3 条。**

1. **HIGH — 已登记的列表退出问题，确实能绕过全部门。**  
   [test_skill_portability_lint.py:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:423)、[`:1907`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1907)：模块将退出列表后的新 fence 当成旧 fence 的 closing，而指纹又不包含 closing 行。

   对照输入：

   ```text
   - ~~~py
     T = "/tmp/cls-exam/x"
     ~~~
   P = "/t" "mp/cls-exam/" "." "./x"
   ~~~
   ```

   **只删除第三行的两个空格。** 本地 CommonMark 对照确认：修改前第四行属于散文；修改后第三行开启顶层 fence，第四行成为可折出 `/tmp/x` 的代码。本模块两边都把第三行当作 closing。

   实测九计数完全相同；越界、可疑、动态、父目录、opaque、URL 全部 `[] → []`；块指纹都为：

   ```text
   B2:0409134db7c0384a
   ```

   这直接证明“实际块划分改变，但指纹集合不变”。**这是已登记缺陷的实际严重性，不是本轮新引入。**

2. **HIGH — 长单元源码保住了，动态消费端仍会把它筛掉。**  
   [test_skill_portability_lint.py:1114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1114)：预筛使用扣重后的 `delta`，但动态检查需要整段源码中的候选。

   安全对照：

   ```python
   if True:
       P = "/t" "mp/cls-exam/x"
       if False:
           pass
       else:
           Q = "/etc/passwd"
   ```

   **仅把最后的 `Q` 改成 `P`**，最终 `P` 就变成 `/etc/passwd`。

   实测短单元候选为 `['/tmp/cls-exam/x']`，长单元 delta 为 `['/etc/passwd']`。整段直接调用 `_has_dynamic_tmp_join()` 得到 **False → True**，但 `dynamic_tmp_join_lines()` 两边均为空：delta 不含 `/tmp`，源码也没有连续的 `/tmp`，因此提前跳过。

   九计数均零，其余正文判据及指纹全部为空。**Counter 没算错；本轮“保留源码”的整改尚未贯通消费端。** 严格 `delta=[]` 的同类反例也成立。

3. **HIGH — bytes 的普通显式常量加法仍完整漏检。**  
   [test_skill_portability_lint.py:655](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:655)、[`:1073`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1073)：`_fold_str()` 只折 `str`，bytes 解码收录的是分散的叶常量，动态扫描也找不到含 `/tmp` 的起点。

   ```python
   # 安全
   P = b"/t" + b"mp/cls-exam/" + b"ok" + b"/x"

   # 只修改一个字面量
   P = b"/t" + b"mp/cls-exam/" + b".." + b"/x"
   ```

   实际路径从命名空间内变成 `/tmp/x`；两侧九计数和全部附加判据仍为零／空。**这是单块、合法 Python、普通常量加法，不需要特殊转义或跨块分析。** 属于既存漏检，本轮 bytes 收录尚未覆盖。

**MEDIUM：**

- **URL 变量出现在路径或 query 中，仍被误认为控制了地址。**  
  [test_skill_portability_lint.py:1841](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1841)：下列输入仍返回“不存在覆盖”：

  ```sh
  curl "${OTHER:-http://localhost:8011}/x?config=${CLS_BACKEND_URL}"
  ```

  `CLS_BACKEND_URL` 不控制主机端口。与正常缺省 URL 对照，九计数及全部附加判据完全相同。去掉 `#fragment` 修复了一个位置，**没有解决变量在 URL 中的作用位置**。

- **`env` 修复出现新回归，也仍有反向误报。**  
  [test_skill_portability_lint.py:1850](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1850)：

  | 输入 | 实际效果 | 当前结果 |
  |---|---|---|
  | `env -i bash -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` | 子 shell 环境已清空 | 漏检；旧分支会抓，属于本轮回归 |
  | `env -u OTHER sh -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` | 没删除目标变量 | 误报；新增规则不检查删除的是哪个变量 |
  | `env -i sh -c "curl ${CLS_BACKEND_URL:-http://localhost:8011}/x"` | 变量已由外层展开 | 仍误报 |

  第一例与正常 URL 的全部正文门签名相同。

- **“剥离注释”只作用于 `env` 分支，赋值／unset 分支仍扫描注释。**  
  [test_skill_portability_lint.py:1820](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1820)、[`:1852`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1852)：给正常 curl 行追加 `# unset CLS_BACKEND_URL` 或 `# CLS_BACKEND_URL=`，仍产生误报。该整改尚未覆盖全部消费分支。

- **登记中的 fence 额度、opening 上下文与散文段界仍有双向错误。**  
  以下反例均无需嵌套容器；这里只证明解析误差，正文修改通常会被指纹接住，不重复计为 HIGH：

  | 位置 | 输入及结果 |
  |---|---|
  | [test_skill_portability_lint.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:403) | `-   ~~~py\n    x\n      ~~~\nZ`：CommonMark 在第三行闭合，模块吞到 EOF。列表间隔不能统一只算一个字符。 |
  | [test_skill_portability_lint.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:283) | `>\t\t~~~py`：CommonMark 是引用内缩进代码，模块却开启 fence；字符数量限制不能替代 tab 列宽判定。 |
  | [test_skill_portability_lint.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:370) | `paragraph` 后紧跟 `2. ~~~py`：有序列表不能在这里打断段落，模块仍开 fence。 |
  | [test_skill_portability_lint.py:629](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:629) | 引用 fence 的内容行 `> > P = …`：第二个 `>` 属于代码，模块仍继续剥除。 |
  | [test_skill_portability_lint.py:528](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:528) | 已有 `2.`、`3.` 两个列表项时，只认 `1.` 的段界会让前项未闭反引号夺走后项 span。 |
  | [test_skill_portability_lint.py:577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:577) | 引用中的空段行 `>` 不被当作空段，同样可能跨段夺走 span。 |

**LOW：**

- **另两项整改仍缺局部承重断言。**  
  [test_skill_portability_lint.py:685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:685)、[`:700`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:700)：分别撤销“只收最外层折叠链”和“追加 bytes 候选”，93 次现有纯测试调用仍全部通过，但直接复现已恢复重复候选／bytes 丢失。[`:2351`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2351) 的空 delta 断言也只证明源码保留，没有证明动态消费端检查了它。

- **code span 空白归一化仍未完成。**  
  [test_skill_portability_lint.py:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:331)：跨行换行、符合条件的首尾空格仍原样返回，可能改变候选及误报。属于已登记 LOW；**这一步本身不需要完整容器栈**。

其余问题的逐项结论：

| 维度 | 复核结果 |
|---|---|
| 相同路径短单元一次、长单元两次 | **未发现相减漏检**；总候选正确为两次。 |
| 成功扩张后再遇 `grown is None` | **未发现已收候选丢失**；后续行仍继续处理。 |
| 长短重叠、最外层 `str +` 折叠 | **未发现当前数量算法错误**。下游预筛问题见 HIGH-2。 |
| 五项新增回退验证 | **均承重**：全量收、只扩一次、两处 40 行限制、空 delta 丢源码，逐个回退均变红。 |
| 所述续接词规则、探针、40 行限制 | 当前已是宽松 `elif/else/except/finally/case` 触发器，不要求冒号；`try` 不在其中；探针和窗口已删除。 |
| `except:`、`except*`、显式续行、heredoc `else/else:` | 所测样本**未发现新漏检**；短单元仍保留。 |
| 无上限扫描吞块、无关语句误吞 | 所测样本**未发现新的候选丢失**；不能由此证明任意输入的成本上界，实际树成本测试未运行。 |
| `With`、推导式、参数、装饰器等 AST 父链 | **未发现节点层新增误放**；HIGH-2 在父链检查之前发生。 |
| 缓存纯度 | **未发现问题**；只依赖 body 文本，缓存 tuple，返回时复制候选列表。 |
| `_shell_words()` | 仍非完整 shell 分词：实测转义引号、未闭引号、NBSP 会误切；反引号内空格也会拆词。当前对应含 `/tmp` 样本的修改仍被段指纹接住。 |
| `_backtick_spans()` opening／closing、转义掩码 | **未发现新的 run 提取缺陷**；空白归一化问题另列。 |
| `_SPAN_SEP_CHARS` | 当前为空，实际只放行空格/tab；已不是中文标点枚举白名单。**未发现本轮新增放行缺口**。 |
| fence 内 `- ` 被散文列表边界切断 | **未发现**；fence body 不进入该散文分段逻辑。 |
| 原文切片与 `start/len(body)` | **未发现错位**；剥前缀不改变行数。当前切片包含 opening，但不包含 closing。 |
| 指纹行序、空白、CRLF、EOF | 已是 **SHA-256 前 16 位**。行序／普通行尾空格改变摘要；CRLF、EOF 换行和纯末尾空行被归一化。未发现该归一化直接造成的新可移植性漏检。 |
| 来源前缀与 U5-B | 格式变化仍可能改变候选数或来源；诊断已解释 `fence/prose` 是提取来源。**未发现本轮新增问题**；不是物理债数量。 |
| U6 交接 | 当前常量检查返回 `[]`，八个交接控制通过；**未发现退化**。 |

**“不含 `/tmp` 的块”边界，实际明显大于少数特殊编码。** 实测保留块 A 的 `T = "/tmp/cls-exam/x"`，仅把块 B 的 `P = T` 改成 `P = "/etc/passwd"`，全部正文门签名不变。这是普通赋值的一行修改。层 3 也仅做文本计数，例如 `P = "/Users" + "/alice/x"` 可以不改变任何脚本指标。这些是范围限制，不能把当前门描述为普遍防止新增可移植性债。

**断言和历史数字：**本次直接调用了 93 个不访问真实正文的测试实例，全部通过；当前三判据表实际 **16 行**、指名形态 **51 对**，未发现既有指名断言失败。r8 的“同字符 closing”和“禁止分号截断”两处变异仍承重。指纹可区分 **45/51**，其余为四例 URL、两例动态拼接；现有 `_NET_ONLY_FORMS` **8/8** 可区分。允许读取面没有原始第九例，因此**不能认证 r13 的“8/9”**，也没有复跑全部 155 项。

残余风险尚不能认定已完整封口：除已声明的容器和跨块边界，仍存在上述静态可确定的漏检及本轮 `env` 回归。

**本轮 BLOCKER 0 条，HIGH 3 条，其中 1 条为已登记未修，2 条为整改仍未封口。**
