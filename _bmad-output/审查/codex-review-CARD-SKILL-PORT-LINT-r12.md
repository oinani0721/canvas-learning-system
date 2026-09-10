**有新回归，当前仍不能收口。** 复核绑定 `2c2b6471320d06b3fccc32947ca844dfb0aba62a`；收尾时被审文件仍与提交一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

以下行号均指 [backend/tests/skills/test_skill_portability_lint.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py)。六条 HIGH 的安全／坏形态均经内存复现：**九计数相同，五项附加结果均为空，新增 URL 判据也为空。**

**BLOCKER：未发现。**

**HIGH：6 条。**

1. **`:659` — 新续接探针拒绝合法的多行 `elif` 头和单行 suite，属于本轮新回归。**

   完整反例：

   ````text
   ```sh
   python3 - <<'PYEOF'
   if False:
       pass
   elif (P := "/tmp/cls-exam/" +
       "." * 2 + "/x"):
       pass
   PYEOF
   ```
   ````

   安全对照仅将 `"." * 2` 改为 `"a"`。坏形态中 `P` 确定指向 `/tmp/x`，但探针只拿续接的第一行加 `pass`，解析失败后在 `elif` 前切开。把分支写成 `elif (P := …): pass` 也漏，因为再追加缩进的 `pass` 反而产生非法缩进。

   **内存恢复整改前的续接函数后，两种形态均重新触发动态判据，证实是红转漏。** 此外，`:651` 只跳空行、不跳同级注释，插入 `# comment` 也能拆断合法续接；这一变体是既存缺口。

2. **`:432`、`:452` — 空白判定仍不符合 shell 词法，清空分隔符表没有完成整改。**

   安全：`执行 P="/tmp/cls-exam/z"`。

   坏形态：

   ```text
   执行 P="/var/cache""/tmp/cls-exam/"<NBSP>`printf a`<NBSP>
   ```

   `<NBSP>` 换成实际 U+00A0；U+3000 同样成立。`isspace()` 放行它们，但 shell 将它们保留在词内，实际路径以 `/var/cache/tmp/…` 开头。

   **只改成 ASCII 空白也不够**：下面的引号内空格会被 `line.split(" ")` 错拆，同样全漏：

   ```text
   执行 P="/var/cache /tmp/cls-exam/ "`printf a`
   ```

3. **`:465`、`:505` — 散文仍跨越真实块边界拼段，前段未闭合反引号会夺走后段合法 span。**

   ````text
   - 段尾 `未闭合
   - 执行 `/var/cache(
     /tmp/cls-exam/x`
   ````

   CommonMark 的第二个列表项拥有独立 code span；当前实现把两个列表项拼起来，真正路径 span 消失。安全对照把第二个 span 换为命名空间内路径。

   **HTML 注释块、单个 `-`／两个 `--` 的合法 setext 下划线也存在同根漏检。** 空行、ATX 标题和部分 thematic break 的修复没有覆盖完整块边界。

4. **`:282` — opening 仍允许任意缩进，四空格代码内容可以错置后续围栏，属于既存未声明漏检。**

   以下第一行有四个前导空格：

   ````text
       ```python
   example
   ```
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ```
   ````

   CommonMark 中第一行是缩进代码，第三行才开启真正围栏；lint 却在第一行开启、第三行关闭，把赋值降成散文。安全对照只改 `"." * 2` 为 `"a"`，全部判据保持不变。

5. **`:895`、`:948` — 重复赋值只覆盖同一单元内的 `Assign(Name)`，静态覆盖仍能绕过。**

   ```python
   P = "/tmp/cls-exam/x"; P: str = "/var/cache/x"
   ```

   第二次赋值是 `AnnAssign`，不进入重复计数；安全对照把最后的字符串换成 `P`。

   另外，即使两次都是普通赋值，只将分号改成换行也能绕过：

   ```python
   P = "/tmp/cls-exam/x"
   P = "/var/cache/x"
   ```

   两行被切成不同单元，最终值明确为 `/var/cache/x`。这不是运行期变量未知的问题。

6. **`:798`、`:1027` — 散文裸 shell 的普通引号拼接仍无判据覆盖。**

   ```text
   安全：P="/tmp/cls-exam/x"
   越界：P="/var/cache""/tmp/cls-exam/x"
   ```

   shell 会把相邻引号内容拼成 `/var/cache/tmp/cls-exam/x`。散文不走 AST／shlex，又没有反引号、反斜杠、`..` 或 `$`，因此全部静默。此前裸 shell 整改只覆盖了特殊记号形态。

**MEDIUM：2 条。**

- **`:287`、`:378` — 本轮 closing 正则的绝对 `{0,3}` 使合法多字符列表围栏无法闭合，新增误报。**

  ````text
  10. ```python
      A = 1
      ```
  此处 `/tmp/cls-exam/x`
  ````

  第三行应正常闭合；当前实现吞入第四行，错误返回 `opaque=[(4, …)]`。后面的 `open_indent + 3` 无法绕过前面的正则，且没有计入列表 marker 的宽度。**此反例已证误报，未证全漏。**

- **`:1606` — `unset` 仍漏掉多变量和引号拼接形态。**

  在原 curl 前加 `unset OTHER CLS_BACKEND_URL;`，九计数及全部附加结果不变，但外部配置已清空。`unset C'LS'_BACKEND_URL` 同样漏。相反，新增选项通配会把仅删除函数的 `unset -f CLS_BACKEND_URL` 误判成清空环境变量。

**LOW：3 条。**

- **`:1923`、`:1930` — 耗时哨兵未清缓存，不能约束首次解析成本。** 前面的基线检查可以预热相同 body；内存验证暖缓存再次调用时，`_parse_units_uncached` 调用数为 **0**。冷解析即使退化，这条计时仍可能绿。
- **`:1646`、`:1665` — 内容指纹实现存在，但声称新增的 `test_opaque_baseline_entries_are_content_bound` 不在最终提交。** 不能把它记为已由专门回归断言钉住。
- **`:900` — 新重复赋值检查会因无关变量产生误报。** `N=1; N=2; P="/tmp/cls-exam/x"` 被判动态拼接，虽然重复赋值的不是路径变量。

其余点名维度逐项结论：

| 维度 | 结果 |
|---|---|
| `lru_cache` 纯度与返回值污染 | **未发现问题。** 正常依赖链不读外部状态；缓存保存 tuple，返回列表另行复制，修改返回值不会污染缓存。 |
| 引用／列表交替、marker 后 tab | **未发现已证的新动态漏检。** 但 `depth` 实际仅当布尔值，无限剥 marker，不是按开启深度剥。 |
| body 引用深度不一致 | 存在容器结束识别差异；**未发现已证的新增静默漏检**，不能称完整符合 CommonMark。 |
| 指纹 `strip()` | 确实忽略首尾空白；针对当前五个登记项，**未发现仅靠这些空白变化即可引入实债的完整反例**。这不证明空白一般没有语义。 |
| 未闭合输入一直尝试到块尾 | **未发现永久吞掉后续候选。** 失败后会退回首行继续扫描；成本仍可能退化。 |
| `_backtick_spans()` 开掩码、闭原串 | **未发现新的漏提 span。** 非 ASCII 标点被多掩本身没有抹掉反引号位置；已证漏检位于分段层。 |
| code span 内容规范化 | 有既存保守误报：两端各补一个空格，CommonMark 内容不变，lint 却可能新增越界候选（`:327`、`:780`）。 |
| `With/withitem/comprehension/keyword/Starred/NamedExpr`、装饰器、默认参数 | **未发现节点层误放。** 有效样本均触发动态判据。 |
| `match/case`、软关键字变量、异步语句、普通 `try/except*` | **未发现问题。** 单行续接 suite 受 HIGH-1 影响。 |
| `\` 续行；已有 `else` 再接 `elif` | 前者**未发现问题**；后者本身不是合法 Python，拒绝它不构成有效程序漏检。 |
| 42 行形态表 | 原断言全部通过；**未发现指名判据错误**。第 15 行 bytes 删除预筛修复后立即失败，确实承重。部分安全对照改变了多处结构，并非全部只差一处。 |
| 两处既有内存变异 | **未发现残留问题。** 删除 fence 同字符条件、恢复分号截断，均使对应断言失败。 |

`fence:`／`prose:` **会随格式调整翻转**：同一路径从 inline 移入 fence，实测由两个 `prose:` 候选变为两个 `fence:` 候选，物理路径数量没有增加。`:1535` 的诊断已经解释这一点，未发现来源前缀本身新增的未说明问题。U5-B 需要同步受影响的计数、越界多重集、行号及内容指纹；U6 scripts 不经过这套来源分类，交接常量纯函数返回 `[]`。

残余风险尚未完整声明：仍有上述可静态确定的漏检，不能认定只剩保守误报与运行期不确定性。

**本轮 BLOCKER 0 条，HIGH 6 条。**
