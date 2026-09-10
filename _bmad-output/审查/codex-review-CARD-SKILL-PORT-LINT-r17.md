复核绑定 **`af2d0faf325f5f79f8b3aa4000a3d82fbe4ddcfd`**；收尾时测试文件与该提交一致，blob 为 `a5b5d6b16cebe566c2334feff53f654d028b4d68`。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：2 条，按根因合并。**

**HIGH-1 — [test_skill_portability_lint.py:804](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:804)，以及 `:814`、`:827`：并集只做一次、且受两个固定窗口限制，合法续接仍会被切断。**

完整静默反例：

````text
~~~sh
python3 - <<PYEOF
if False:
    pass
elif False:
    pass
elif (P := "/t" "mp/cls-exam/" + "." + "./x"):
    pass
PYEOF
~~~
````

第一次扩张收进第一个 `elif` 后立即结束；第二个 `elif` 独立退给 `shlex`，Python 拼接关系丢失。实际 `P` 为 `/tmp/cls-exam/../x`，规范化为 `/tmp/x`。

安全对照仅将 `"."` 改成 `"a"`。实测两者**九计数全零，越界、可疑行、动态拼接、父目录、不透明、URL、块指纹全部为空**。这是同一合法 Python 语句内的漏检，超出了跨块数据流边界。

两个窗口也分别承重失败：

| 形态 | 能抓 | 全部静默 |
|---|---:|---:|
| `if False:` 和首个 `pass` 后，再放体内 `pass`，随后接坏 `elif` | 39 行 | 40 行 |
| `elif (` 后放注释，再接赋值表达式、`):`、`pass` | 37 行注释 | 38 行注释 |

因此，“歧义取并集”的方向成立，当前实现尚未覆盖完整续接链。

**HIGH-2 — [test_skill_portability_lint.py:524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:524)、`:570`、`:1848`：空列表项被错误断段，语义判据与指纹共同失明。**

安全输入如下；**第二行精确为 `+ `，末尾有一个 ASCII 空格**：

```text
执行 `P = (""
+ 
"/tmp/cls-exam/x")`
```

坏输入只将第一行 `""` 改成 `"/var/cache"`。

本地 CommonMark 解析确认：空列表项不能打断段落，两者都是一个完整 code span；其中的 Python 表达式分别得到：

- 安全：`/tmp/cls-exam/x`
- 越界：`/var/cache/tmp/cls-exam/x`

模块却把第一行单独切走，仅给第 2–3 行绑指纹。两者九计数相同，六项语义输出全部为空，指纹也完全相同：

```text
['S2:28d0a904a49e0933']
```

同根还有 `1. ` 空列表项，以及被 `\s` 错认成标题的 `#<NBSP>x`。这证明兜底网确实会继承错误分块，且不需要特殊编码或跨块分析才能触发。

**MEDIUM：3 条。**

**MEDIUM-1 — [test_skill_portability_lint.py:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:818)、`:845`，消费端 `:895`：短长单元重叠会重复计候选，能够形成可抵消额度。**

在 shell fence 的 Python heredoc 中使用：

```python
if True:
    P = "/t" "mp/old.json"
else:
    pass
```

再保持行数，将最后两行替换为：

```python
Q = "/t" "mp/old.json"
pass
```

前者只有一处路径，被短、长单元各计一次；后者有两处路径，各计一次。两者越界多重集均为：

```text
fence:/tmp/old.json × 2
```

九计数均零，其余判据及指纹全部为空。因此，**候选变多并非始终只有误报后果，登记后的重复候选确实可以抵消新增路径**。未据此推断禁读正文已经包含这种形态；含字面 `/tmp` 的对应修改仍会被块指纹接住。

**MEDIUM-2 — [test_skill_portability_lint.py:1783](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1783)：同词出现变量，仍不能证明后端地址受该变量控制。**

将安全 URL：

```sh
curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
```

替换为：

```sh
curl "${OTHER:-http://localhost:8011}/x${CLS_BACKEND_URL:+}"
```

`${CLS_BACKEND_URL:+}` 无论变量是否设置都展开为空，后端地址实际不受它控制；两者九计数及全部附加输出仍相同。

手写分词也不识别命令分隔符，下面这个合法形态同样静默：

```sh
curl "${OTHER:-http://localhost:8011}/x";URL="${CLS_BACKEND_URL}"
```

此外，`env -i sh -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` 会先清空环境、再由子 shell 展开变量，当前也未检出。新增的 `env -u CLS_BACKEND_URL` 检查没有覆盖这一面。

**MEDIUM-3 — [test_skill_portability_lint.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:291)、`:398`、`:420`：引用 fence closing 仍双向判错，opening 自身缩进仍会混入额度。**

以下用 Python 字符串表示精确输入：

```python
"> ~~~python\n> X\n>    ~~~\nY"
```

CommonMark 会闭合；模块不闭合。`>` 后四个空格包含一个标记空格和合法的三列内容缩进，但 closing 正则只接受三个字符。

反方向：

```python
">   ~~~python\n> X\n>\t  ~~~\n> P = 2\n> ~~~\nY"
```

第三行在 CommonMark 中不闭合：引用后的内容缩进为四列。模块却将 opening 的整个前缀宽度 `4` 当容器基线，以 `6 <= 4 + 3` 提前闭合，最后甚至把 `Y` 收进错误开启的新 fence。

这两处可以与已登记的容器风险合并处置，但**不能认定本轮额度已经正确**；定位这两个反例也不需要完整容器栈。

**LOW：1 条。**

**LOW-1 — [test_skill_portability_lint.py:2193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2193)：新增“并集”局部断言仍未证明关键修复有效。**

独立内存变异结果：

| 变异 | 结果 |
|---|---|
| 恢复旧续接正则 | 原 51＋8 形态及新增续接断言，**60/60 仍通过** |
| 成功扩张后丢掉短单元，只保留长单元 | 新增续接断言仍通过 |
| 恢复“无容器也给 opening 缩进额度” | 新增 fence 断言立即失败，确实承重 |

续接测试只断言存在长单元及其折叠值，没有检查短单元存在，也没实际检验合法的 `else \` 换行 `:`。因此上一轮强调的局部断言问题只修好了一半。

其余问题逐项结论：

| 维度 | 复核结果 |
|---|---|
| 当前续接词规则／探针 | 当前是宽关键词触发器，已不要求冒号，也没有活动中的占位 `pass` 探针；主要缺陷见 HIGH-1。 |
| 不完整 Python 扫到块尾 | **未发现失败后吞掉整块候选的新漏检**。失败后未推进 `i`，仍会回退检查；长单元的重复解析成本仍存在。 |
| AST 的 `With`、默认参数、装饰器、comprehension、keyword、Starred、NamedExpr | 已验证样本中，**未发现节点层新的误放**；前置切分仍受 HIGH-1 影响。 |
| `lru_cache` | **未发现外部状态依赖或返回值污染**；修改返回的候选列表不影响下一次读取。 |
| fence 内以 `- ` 开头的代码 | **未发现被散文段逻辑再次切分**；前提是 fence 已被正确识别。 |
| 引用／列表交替、tab、深度变化 | 已登记的容器识别限制仍存在；不能仅凭 `expandtabs(4)` 认为容器基线正确，见 MEDIUM-3。 |
| 原文行切片 | **未发现新的行号对应错误**。剥前缀不改变 body 元素数量；当前切片还包含 opening，已经不是提问中的旧切片。 |
| 指纹空白与换行 | 当前为 **16 位摘要，不做 `strip()`**。行序、行尾空格和 tab 改变会影响摘要；经正式分块后 LF／CRLF、文件末尾换行及块尾纯空行被归一化，未发现新的不稳定。 |
| `_backtick_spans` 掩码、opening／closing | **未发现可确认的新漏检**；这不构成完整 CommonMark 等价证明。已确认的段级缺口见 HIGH-2。 |
| `_shell_words` | 仍非完整 shell 分词；转义引号、Unicode 空白等现有样本依靠指纹兜底。URL 中的实际静默见 MEDIUM-2。 |
| `_SPAN_SEP_CHARS` | 当前为空，仅空格／tab 放行；**未发现枚举遗漏造成的新漏检**，标点紧贴造成的保守误报仍在。 |
| 来源前缀与交接 | **未发现 Counter 算法或交接常量新问题**；`check_handoff_constants()` 返回 `[]`。格式变化可以翻转来源，现有诊断已说明它不等于物理债增减。 |
| 形态表承重 | 三判据表当前 **16 行**、演进形态表 **51 行**，逐项通过。部分安全对照改变了结构，未严格只差一处；本轮未发现因此造成的指名判据归因失效。 |
| r13 的“8/9” | 当前 `_NET_ONLY_FORMS` **8/8** 可由指纹区分，其中三对现在也被语义判据抓到。允许读取的材料没有原始九例全集，故不能独立确认历史 **8/9**。 |
| 当前树是否仍全绿 | 未运行全树测试、未读禁读正文，**不能据这些纯函数结果确认 154 条全绿或树上没有新增误报**。 |

“不含字面 `/tmp` 的块”这个残余面，**远大于跨块数据流和少数特殊编码**。[`:645`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:645)、`:1068`、`:1835` 的组合，连同一块中的普通表达式也会漏：

```python
# 安全 → 越界；两对均全部静默
P = "".join(("/t", "mp/cls-exam/x"))
P = "".join(("/t", "mp/x"))

P = Path("/") / "tmp" / "cls-exam" / "x"
P = Path("/") / "tmp" / "x"
```

跨块的普通 `os.path.join(P, "x")` 改成 `os.path.join(P, "..", "x")` 也已复现全部不变。因此可以将这类能力边界登记不修，但必须按**整类无字面 `/tmp` 的路径构造与后续使用**理解；不能据当前门宣称所有新增可移植性债都会报红。常量链中间值造成的保守误报可以保留；本轮另有 HIGH-1、HIGH-2 这两条超出既有解释的确定性漏检。

**本轮 BLOCKER 0 条，HIGH 2 条。**
