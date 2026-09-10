复核绑定 **`798bbef7b2688c5114bc9ad08ac0d80b2dbff07e`**；收尾时限定代码仍与提交一致，测试文件 blob 为 `d4896c334edaa940db0abed211bcb816b84192d5`。全程只读，未跑 pytest、读取禁读正文或连接网络／数据库。CommonMark 对照使用本地 `MarkdownIt("commonmark")` 内存解析。

**围栏算法仍未修对；另有散文分段和续接判定的完整静默反例。** 下列行号均指 [test_skill_portability_lint.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py)。

**BLOCKER：未发现。**

**HIGH：3 条，按根因合并。**

1. **HIGH — [同文件:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:419)、`:415`、`:1825`：closing 仍忽略引用标记后的缩进，且 closing 改动不进指纹。**

   安全输入：

   ```text
   > ~~~sh
   > set +e
   > P="/tmp/cls-exam/x"
   > ~~~
   > P="/etc/passwd"
   > ~~~
   ```

   **只把第四行改成 `> \t\t~~~`，其中 `\t` 是真实 tab。**

   - CommonMark：第四行不能闭合；第五行进入原 shell 代码块。`set +e` 下，中间 `~~~` 命令即使失败，后续赋值仍执行。
   - 本模块：`_indent_cols()` 只数首个 `>` **之前**的缩进，得到 **0**，错误闭合。
   - 实测九计数相同，越界／可疑／动态／父目录／opaque／URL 输出均为空；指纹同为 **`B2:ee34e35110efb201`**。
   - CommonMark 的 fence 区间由 `[0,4]` 变成 `[0,6]`，模块完全看不见这个归属变化。

   **另一个入口：**普通 closing `~~~` 后添加 NBSP、VT 或 FF。`:415` 的 `.strip()` 接受它们，CommonMark closing 尾部只接受空格／tab；同样能改变代码归属而保持全部门不变。

   因此，“无容器基线为 0”修正成立，但**closing 一侧的实际列数及尾部字符判定仍错**。

2. **HIGH — [同文件:519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:519)、`:562`、`:565`、`:1829`：散文被错误切段后，第二段改用途仍能绕过段指纹。**

   安全输入是一个跨行 code span：

   ```text
   执行 `P="/tmp/cls-exam/
   2. /x"`
   ```

   只将第二行替换为：

   ```text
   2. /../../x"`
   ```

   CommonMark 中，**`2. ` 不能打断已经开始的段落**，两行仍属于同一个 span。换行归为空格后，路径由命名空间内变成 **`/tmp/x`**。

   本模块却把第二行一律当成新列表项：

   - 两个段均提不出完整 span；
   - 第二段不含 `/tmp`，不进指纹；
   - 九计数和全部附加输出不变，指纹均为 **`S1:6ca0e6d5f00a778c`**。

   同根还有 **NBSP-only 行被 `.strip()` 当空行**，而 CommonMark 不把它当空行，同样会拆断合法 span并放过后段改动。

   反方向也仍有：`<!-- … -->` 结束后没有断段、setext 的 `--` 未识别，会让前段未闭合反引号夺走后段 opening。后两种实测样例由整段指纹接住，未另计 HIGH。

3. **HIGH — [同文件:684](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:684)、`:747`、`:816`：续接词规则仍误认合法 heredoc 终止符，并切断合法 Python 显式续行。**

   以下内容外包 `~~~sh` 围栏：

   ```sh
   python3 - <<'else:'
   if False:
       pass
   elif P := "/t" "mp/cls-exam/" "." "./x":
       pass
   else:
   echo done
   ```

   安全对照**只把 `"."` 改成 `"a"`**。Python 的实际常量由 `/tmp/cls-exam/a./x` 变成 `/tmp/cls-exam/../x`。

   `else:` 是合法 shell heredoc 终止符，却被当成 Python 续接；已经成功解析的复合语句最终降级到 shlex，隐式拼接丢失。**实测九计数全零，六项语义输出和指纹全部 `[] → []`。** 这里没有跨块数据流；源码拆字使兜底网也不覆盖。

   另一方向，合法 Python：

   ```python
   else \
   :
   ```

   被新正则拒绝续接。标准 heredoc 内的对应样例，普通 `else:` 能触发动态判据，改成上述合法续行后变成空结果。**这是本轮限制冒号位置引入的回归。**

**MEDIUM：2 条。**

1. **MEDIUM — [同文件:1768](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1768)：出现展开语法仍不能证明该展开用于目标 URL。**

   ```sh
   # 安全
   curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"; : "${CLS_BACKEND_URL}"
   # 坏
   curl "${OTHER:-http://localhost:8011}/x"; : "${CLS_BACKEND_URL}"
   ```

   **全部计数、附加输出及指纹相同。** `CLS_BACKEND_URL` 确实展开，但没有用于 curl；放在 `# ${CLS_BACKEND_URL}` 注释里也能放行。

   此外，`env -u CLS_BACKEND_URL sh -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` 会确定性删除传入配置，当前赋值／`unset` 检测也漏掉。该边界不局限于特殊编码。

2. **MEDIUM — [同文件:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:283)、`:397`、`:595`：容器识别缺少上下文，剥前缀也未遵守实际深度。**

   - `>    ~~~python`：quote 标记后一个空格，加合法 opening 缩进三个空格；CommonMark 开 fence，模块漏开。
   - `- item` 后的列表延续行以两空格开启 fence、五空格 closing：CommonMark 正常闭合，模块把基线设成 0，吞入后文。
   - `10. item` 后四空格开启的列表内 fence，模块整个漏开。
   - `-     ~~~python` 应为列表内缩进代码，模块反而开 fence。
   - `> ~~~sh` 内的 `> > "/tmp/cls-exam/x"`，第二个 `>` 是代码中的重定向；模块继续剥掉它。`depth` 实际只作布尔判断。

   上述具体改动由原文指纹接住，未发现另一条完整静默链。

**LOW：2 条。**

1. **LOW — [同文件:2238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2238)、`:2288`、`:3385`：两张形态表没有钉住本轮两处关键修复。**

   内存分别恢复旧续接正则、恢复“无容器也给 opening 缩进额度”，**51 条指名形态＋8 条兜底形态仍为 59/59 通过**。前者已重新产生 heredoc `else` 的语义漏检，但兜底表只比较指纹。

   这证明局部回归断言缺失；**不能据此声称完整 152 项测试都放过**，真实树正控未运行。

2. **LOW — [同文件:656](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:656)：常量链同时提交中间值，造成既存保守误报。**

   `P = "/tmp/cls-exam/" + "../" + "cls-exam/x"` 最终路径合规，但中间 `/tmp/cls-exam/../` 也被作为候选，误报 `fence:/tmp`。

其余问题逐项结果如下：

| 维度 | 复核结果 |
|---|---|
| 原文 `start/len(body)` 切片 | **未发现独立错位。** 每个物理 body 行仍对应一次 append；问题在分块边界。 |
| 指纹的 `strip()`／sha8 | 当前实际为 **SHA-256 前16位、仅去末尾 CR/LF**。行序、实际行尾空格变化会改摘要。 |
| CRLF、EOF 换行、块末纯空行 | 普通 fence 实测指纹稳定；含空格或引用标记 `>` 的空行会改变摘要。未发现独立不稳定问题。 |
| fence 内以 `- ` 开头 | 普通 fence **未发现**被散文列表边界拆开；容器内过度剥除见 MEDIUM-2。 |
| marker 后 tab、容器交替 | `-\t~~~`、`> - > ~~~`、`- > - ~~~` 的简单样例正常；不能据此证明所有组合正确。 |
| AST 探针与 `pad` | 当前执行代码**没有该探针**；不存在可供本轮评判的 `pad` 行为。 |
| `except:`、`except*`、多行 `elif/except`、`match/case`、异步语句 | 测试的合法样例**未发现额外漏检**。显式续行例外见 HIGH-3。 |
| 未完成语句一直读至块尾 | **未发现单独导致后续候选永久丢失。** 失败后会退回继续处理，循环有限；重复解析成本仍存在。 |
| `case = 0` 吞无关语句 | 已声明成本面成立：200 行合成一个单元；未另找到完整静默反例。 |
| `With/withitem`、推导式、`keyword`、`Starred`、`NamedExpr`、装饰器、默认参数 | **未发现 AST 节点层误放**，逐类有效样例均触发动态判据。 |
| `_backtick_spans()` 掩码与 run 扫描 | 对反斜杠／反引号组合的 **9,840 个短样例**与 CommonMark 对照，未发现多提／少提；不涵盖前置分段错误。 |
| `_shell_words()` | 仍不能正确处理全部转义引号、NBSP、未闭合引号及反引号内空格；`$'…'` 也没有真实展开语义。含字面 `/tmp` 的已测变更由指纹接住，未发现额外独立绕过。 |
| `_SPAN_SEP_CHARS` | 当前为空，只放行空格／tab。中文标点遗漏造成的保守误报仍在，未发现新的白名单放行缺口。 |
| `lru_cache` | **未发现纯函数或结果别名问题**；缓存只依赖源码，外层复制返回列表。 |
| 来源前缀 | `prose:`／`fence:` 表示模块的提取来源，不能直接当成实际代码归属；错分会翻转标签。未发现独立于已报分块问题的新缺陷。 |
| U5-B／U6 交接 | U5-B 仍需同步受影响的各项基线，不能只更新九计数；U6 交接常量检查返回 `[]`，未发现新问题。 |

**不含 `/tmp` 的块，其静默面确实远大于少数编码形式。** [同文件:1816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1816) 的过滤允许：

```python
# 第一块保持不变
T = "/tmp/cls-exam/x"

# 第二块
P = T
# 替换为
P = T.replace("cls-exam/", "")
```

按两块顺序使用时，路径变成 `/tmp/x`；**九计数、所有语义输出及指纹全部不变**。这覆盖普通后续变量使用、字符串处理和重新赋值。它属于本次已明确接受的跨块边界，不重复计入新增 HIGH；前三条 HIGH 则不能用这个声明解释。

断言与数字的独立结果：

| 项目 | 结果 |
|---|---|
| 指名形态表 | **51/51** |
| 当前兜底表 | **8/8**，NBSP 前提确实检查 U+00A0 |
| 指纹覆盖 | **45/51**；未区分的是 **4 个 URL／unset＋2 个拆字 Python** |
| “15 行”三判据表 | 当前实际 **16 行，16/16 通过** |
| 同字符／分号截断内存变异 | 对应断言均失败，**承重** |
| 两个正式消费门恒返 `[]` 的变异 | 对应负控均失败，**承重** |
| “至少有人红” | 被前面的指名断言逻辑蕴含，**没有额外承重** |
| 测试数 | 静态展开为 **152**；未做 pytest collect 或执行 |
| 历史 r13 的 8/9 | **无法独立确认**：允许材料中缺少那九个原始样本，不能用当前 8/8 替代 |

残余风险尚未完整收口：仍存在可静态确定、全部门都保持不变的未声明漏检。

**本轮 BLOCKER 0 条，HIGH 3 条。**
