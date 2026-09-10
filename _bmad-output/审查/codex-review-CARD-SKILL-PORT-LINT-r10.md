复核绑定 **`f4dacfe3beda16a8f160b84257ed98087a0fa6ca`**；被测文件 blob 与提交一致，为 `376afd4bbf56c60fd667bfdd40c938f7bb993b6e`。完成限定范围内的读取及纯函数、内存变异验证，未运行 pytest、修改文件或连接服务。

**BLOCKER：未发现。**

**HIGH：6 条，按根因合并。** 以下主反例均存在九项计数相同、**六项附加结果全部 `[] → []`** 的替换对照，包含新增 URL 判据。

1. **HIGH — [test_skill_portability_lint.py:311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:311)：closing 只检查右边界，会用较长反引号串的尾部提前闭合；这是新回归。**

   精确输入：

   ```text
   `p ```/var/cache(/tmp/cls-exam/x```
   ```

   初始单反引号没有匹配，后面的三反引号本应形成合法 span；当前却提取 `['p ``']`，真正的路径 span 消失。按整改 diff 在内存恢复旧函数后，能正确提取 `/var/cache(/tmp/cls-exam/x`。

2. **HIGH — [test_skill_portability_lint.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:487)：整体剥容器前缀会同时删除 Python 的真实缩进；这是新回归。**

   ```text
   > ```python
   > def f(p = "/tmp/cls-exam/" + "." * 2 + "/x"):
   >     pass
   > ```
   ```

   当前 body 中的 `pass` 已无缩进，函数定义解析失败，默认参数中的越界运算随之漏掉。保留示例中的 `p =` 空格即可复现六项全空；恢复 diff 中旧 stripper／旧窗口实现后，动态判据能抓到第 2 行。

   此外，`depth` 现在实际上只是开关：传入 `1`、`2`、`3` 都会剥尽全部 `>` 与空白。body 多出的引用符也被删除；body 少一层时，旧容器不会及时结束，后续顶层 fence 会被继续吞入。

3. **HIGH — [test_skill_portability_lint.py:614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:614)：仅查看紧邻下一行，仍会在复合语句第一分支尚未结束时认走单元。**

   放入 shell fence 的 Python heredoc：

   ```sh
   python3 - <<'PYEOF'
   if False:
       pass
       pass
   elif (P := "/tmp/cls-exam/" + "." * 2 + "/x"):
       pass
   PYEOF
   ```

   第一个 `pass` 后就切开，`elif` 头降级到 shlex，最终 `/tmp/x` 全漏。将 `2` 改为 `0` 是等计数合规对照。第一分支与 `elif` 之间插入空行或注释也能复现；这是续接整改尚未覆盖的缺口。

4. **HIGH — [test_skill_portability_lint.py:468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:468)：散文合并没有遵守 Markdown 块边界，前一段的未闭反引号能夺走后一段的合法 opening。**

   ```text
   段尾 `未闭合

   执行 `/var/cache(
   /tmp/cls-exam/x`
   ```

   当前只提取 `['未闭合\n\n执行 ']`；删除前面的无关段落，真正的越界 span 才重新出现。列表项、表格后的空行、HTML 注释也复现同类漏检。反方向也成立：跨空行拼出不存在的 span，造成新误报。

   另一个边界错误是：`_fence_blocks()` 已判为 prose 的多反引号 inline 行，仍被这里仅凭 `_FENCE_OPEN_RE` 当成 fence 标记丢弃；因此你自查修复的“标记行不能并段”，目前判断范围过宽。

5. **HIGH — [test_skill_portability_lint.py:410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:410)：分隔符表仍含 ASCII `*`，新增中文引号也能属于 shell 词，继续放行嵌入式命令替换。**

   ```text
   执行 P="/var/cache""/tmp/cls-exam/"*`printf a`*
   ```

   赋值结果为 `/var/cache/tmp/cls-exam/*a*`，但六项全空。把两侧 `*` 换成新增的 `“`、`”` 也全漏。

   `*` 属于本轮声称已修、实际仍残留的形态；新增中文引号扩大了同类缺口。真正危险的是把合法 shell 词字符当作安全边界。

6. **HIGH — [test_skill_portability_lint.py:814](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:814)：原始源码必须含 `/tmp` 的预筛，会挡掉 AST 已经能够识别的隐式字符串拼接；这是既存未声明漏检。**

   ```python
   P = "/t" "mp/cls-exam/" + "." * 2 + "/x"
   ```

   `_has_dynamic_tmp_join()` 单独调用返回 **True**，但外层根本不调用它；九计数全部为零，六项附加结果全部为空，实际路径规范化为 `/tmp/x`。只将 `"."` 改成 `"a"`，计数与结果完全不变。这里没有运行期变量或来源额度抵消。

**MEDIUM：1 条。**

- **MEDIUM — [test_skill_portability_lint.py:1447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1447)：新增 URL 正则只识别赋值，漏掉确定性清空配置的 `unset`。**

  ```sh
  unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"
  ```

  相比没有 `unset` 的同一行，九计数与六项附加结果完全相同，但外部配置已被取消，必走 localhost。这是上一轮 URL 意见的同根未修完。

**LOW：3 条。**

- **LOW — [test_skill_portability_lint.py:2524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2524)：r9HIGH-1a 形态表不承重。** 内存把 `_PY_CONTINUATION_RE` 改成永不匹配，指名断言仍通过，因为 `else` 内的独立赋值被单独解析后照样得到 `/tmp/x`；它没有检验必须依附续接头才能解析的危险表达式。

- **LOW — [test_skill_portability_lint.py:2552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2552)：r9HIGH-3b 使用了错误的容器样本。** 三行都写 `- >`，实际是三个列表项；同一列表项内的合法形态应仅首行用 `- >`，后续用 `  >`。当前断言依赖把不同列表项错误揉成一个 fence，不能证明其声称的嵌套支持。

- **LOW — [test_skill_portability_lint.py:604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:604)：无上限窗口的 O(n) 声明不成立。** 合法长括号单元每轮重复 join、dedent、AST 和 compile；1000／2000／4000 行注释实测约 `0.11／0.39／1.45s`，呈二次增长。这些样本均完整提取，未据此另报漏检。

其余维度逐项结论：

| 维度 | 复核结果 |
|---|---|
| `_py_needs_more()` 一直 True 到块尾，直接丢掉后续候选 | **未发现。** Python 失败期间 `i` 不移动，随后从原位置重试 shell，最终仍可单行回退。 |
| 去掉 200 行限制后的长合法单元 | **未发现漏检。** 验证至 4003 行仍完整提取。 |
| `With/withitem/comprehension/keyword/Starred/NamedExpr`、装饰器、默认参数 | **未发现 AST 父链本身误放。** 已证问题在前置切分、缩进剥离和原串预筛。 |
| Python `\` 续行、`async def`、`async with` | **未发现所测合法样本漏检。** |
| opening 转义掩码过度匹配非 ASCII 标点 | **未发现独立丢 span。** 多掩的非反引号字符不改变 tick 位置；确定缺陷是 HIGH-1 的 closing 边界。 |
| 枚举表遗漏中文分隔符 | 全角 `［］｛｝` 等遗漏会偏向误报；**未发现由这些遗漏本身造成的漏报**。表内字符导致的漏报见 HIGH-5。 |
| `fence:`／`prose:` 来源翻转 | **会因格式调整报红。** 同一 `/tmp/legacy` 从 inline 改为 fence，实测两条 `prose:` 变成两条 `fence:`。新增说明已解释来源翻转，未发现 Counter 算法新问题。 |
| U5-B／U6 交接 | U5-B 仍须同步受影响的越界多重集和行号基线，不能只改 `QUIZ_ANSWER_BASELINE`。U6 scripts 不经过该来源 Counter；交接常量纯函数返回 `[]`。 |
| 25 行现有形态表 | 指名断言直接调用均通过；其中两条证据问题见 LOW。部分安全对照仍非严格只差一处。 |
| 两处内存变异 | **未发现承重问题。** 删除 fence 同字符条件、恢复候选分号截断，均使对应断言失败。 |
| 安全参数的 `fence:` 前缀修正 | **未发现残留问题。** |
| “至少有人红”断言 | 指名断言通过后必然成立，没有额外承重，不另计缺陷。 |
| 已接受的同来源内部抵消 | 按已声明设计取舍处理，未重复计入本轮问题。 |

残余风险**尚未完整声明**：仍有明确的新回归，以及与已接受抵消取舍无关、可静态确定的漏检。

**本轮 BLOCKER 0 条，HIGH 6 条。**
