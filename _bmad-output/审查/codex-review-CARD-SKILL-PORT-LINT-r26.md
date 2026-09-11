**本轮确有回归：3 条新增漏检、2 组新增误报；另有 1 条既存 HIGH 未闭合。**

复核绑定 `6540e409fab5f00a962f94ebf624eac42adfa041`，测试文件 blob 为 `ab9cc6fb85d5d6c1e52aae4c94557863f6851121`，收尾核对一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库；旧版通过授权 diff 在内存逆向还原。

**BLOCKER：未发现。**

**HIGH：4 条。**

1. **新增回归 — [test_skill_portability_lint.py:1640](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1640)：缺少结束标记时，真实 Python heredoc 的重赋值关系被丢弃。**

   ````text
   ```sh
   python3 - <<'END'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   ```
   ````

   `dynamic_tmp_join_lines()`：旧版 `[(4, 'P = "/etc/passwd"')]`，新版 `[]`。把 `END` 放到下一 fence，同样旧抓新漏。

   **当前回落方向不成立**：shell 开启行使整块 Python 解析失败，逐语句解析又无法关联两次赋值。可以保持“不跨 fence 串联”，但已识别的 Python stdin heredoc 缺尾时，应保留当前块尾部作为候选执行区，或明确登记“不完整”。

   同根既存缺口也仍在：合法 Python 的四行 `合规赋值 → N = 1 << 2 → 2 → 越界赋值`，会因存在独立表达式行 `2` 而被误认成 heredoc，两版均漏。**结束标记存在仍不足以证明 heredoc 解释成立。**

2. **新增回归 — [test_skill_portability_lint.py:1580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1580)：扫描整个短选项词中的 `c/m`，会侵入带参数选项的参数内容。**

   ```sh
   python3 -Wignore::DeprecationWarning - <<'END'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   END
   ```

   新版把 `DeprecationWarning` 内的 `c` 当成 `-c`，返回脚本 `'ationWarning'`，取消真正的 stdin 执行区。动态判据旧版命中第 4 行，新版 `[]`。`-Xpycache_prefix=/cache` 同样漏检。

   短选项需要按顺序识别；遇到消费参数的选项后，余下字符不能继续当选项扫描。

3. **新增回归 — [test_skill_portability_lint.py:1426](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1426)：括号包裹的仅注解被误收为局部绑定，导致 `nonlocal` 改写归错作用域。**

   ```python
   def outer():
       P = "/t" + "mp/cls-exam/x"
       def middle():
           (P): str
           def inner():
               nonlocal P
               P = "/etc/passwd"
           inner()
       middle()
       return P
   ```

   树内 Python 的 `compile`／`symtable` 确认：`P: str` 产生局部绑定；`(P): str` 的 `AnnAssign.simple=0`，**不产生该绑定**。新版只检查目标为 `Name`，错误地让改写停在 `middle`。

   动态判据旧版 `[(8, 'P = "/etc/passwd"')]`，新版 `[]`。这次仍是“新增判据太宽”，但结果是漏检。

4. **既存缺口 — [test_skill_portability_lint.py:1176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1176)、[同文件:1122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1122)：直接出现的命名空间写入仍有静默形态。**

   在合规的 `P = "/t" + "mp/cls-exam/x"` 后追加任一项：

   ```python
   import sys
   sys.modules[__name__].P = "/etc/passwd"
   ```

   ```python
   globals().__ior__({"P": "/etc/passwd"})
   ```

   第一项实际写入目标是 `Attribute`，目标检查只认 `Subscript`；第二项不在 `_NS_MUTATORS`。两版均漏。这些机制直接出现在当前块中，登记它们不需要跨过程数据流分析，应在本卡处理。

   `del P`、`del globals()["P"]`、`globals().__delitem__("P")` 也仍静默：识别“名字成为局部绑定”并不等于识别“已有绑定被删除”。删除不直接等同于路径外逃，不另计 HIGH。

以上 HIGH 主反例均完成安全负控：将坏写入目标改为 `Q`，九项计数保持相同；其余附加判据均无兜底。由于常量分写成 `"/t" + "mp/…"`，**第十条块指纹也为空**。

**MEDIUM：2 条。**

1. **新增误报 — [test_skill_portability_lint.py:1158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1158)、[同文件:1163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1163)、[同文件:1176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1176)：反射识别混淆了方法名、读取来源和实际写入目标。**

   同块存在合规 `P` 时，下列形态均由旧版 `[]` 变成新版报红：

   | 输入 | 误判原因 |
   |---|---|
   | `page.reload()` | 任意 `.reload` 被当成模块重载 |
   | `config = {}; config.update(globals())` | 读取模块字典、写入新字典，被当成修改模块字典 |
   | `config.update(vars(args))` | 普通对象配置合并也被认作模块写入 |
   | `args.__dict__["verbose"] = True` | 实例属性字典被等同于模块命名空间 |
   | `cache[globals()["P"]] = 1` | 整棵目标遍历未区分 `Load/Store`，读取下标键被当成写入 |

   任意业务属性 `.modules[…]` 也被同样扩大识别。真实九份正文零命中不能量化这些误报面；上述反例已经证明它们存在。

2. **新增误报 — [test_skill_portability_lint.py:2796](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2796)：逐词循环没有真正定位命令词，普通参数 `unset` 仍被当成命令。**

   ```sh
   printf '%s %s' unset C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   这里只打印两个字符串，没有删除变量；`_url_override_hit()` 却由旧版 `False` 变成新版 `True`。另外，`unset '-f' C'LS'_BACKEND_URL` 也被误报：变量词去引号了，选项词没有一致处理。

**LOW：未发现独立新增问题。**

其余维度明确结论：

| 维度 | 结果 |
|---|---|
| 重定向引号掩码、分隔符转义掩码 | **未发现独立新增回归** |
| `import`、`for`、`with as`、`except as`、`match`、嵌套 `def/class`、形参、普通仅注解、`del` 的绑定收集 | **未发现这些类别漏收**；它们已由 `_assignments()` 或本轮补充覆盖 |
| 新测试是否承重 | **未发现问题**；直接调用通过，11 个独立内存撤回探针均使对应断言失败 |
| 交接常量与相关契约 | **未发现问题** |
| start-exam-board 的路径、建目录及 URL 整改 diff | **未发现问题** |

本卡与另卡的分界还需收紧：上面的词法识别、`AnnAssign.simple`、直接命名空间写入及明确只读负控，应在本卡完成。跨 fence 的执行关联、完整控制流／别名分析、运行时展开和 symlink 落点，可以另立卡。你声明的提前离开保守面，本轮不重复计缺陷。

**本轮 BLOCKER 0 条，HIGH 4 条。**
