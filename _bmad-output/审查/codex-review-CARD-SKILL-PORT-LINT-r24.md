复核绑定 **`e22c6d2718edc222088abebb907d69d8c25f01b9`**；收尾时测试文件 blob 仍为 `8c13199ea67c46550939751d63d4b3e3635963cc`，与提交一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**默认方向正确，但目前的沉默条件还不够严。** “没有名单中的祖先”并不等于必经，而且写入记录仍不完整。

以下 HIGH 主反例均使用 `"/t" + "mp/cls-exam/x"`：九项计数不变，五项路径判据、URL 判据及第十条块指纹均返回 `[]`，并非只绕过某个 helper。

**BLOCKER：未发现。**

**HIGH：6 条。**

1. **[test_skill_portability_lint.py:1098](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1098)、`:1355`：祖先黑名单不能证明后写必经。**

   ```python
   from contextlib import suppress
   P = "/etc/passwd"
   with suppress(ZeroDivisionError):
       1 / 0
       P = "/t" + "mp/cls-exam/x"
   ```

   实际最终 `P == "/etc/passwd"`，却全部静默。仅将 `1 / 0` 改成 `1 / 1`，实际值变合规，判据仍完全相同。

   同根反例还有：函数在合规赋值前已经 `return P`；以及未列入 `_CONDITIONAL_NODES` 的 `TryStar`，其 `except*` 吞掉异常后跳过合规赋值。这些都满足**当前实现检查的**四条件。

   短路表达式、空推导式也能骗过这个 helper，但已被动态表达式判据兜住，未另计漏洞。

2. **[test_skill_portability_lint.py:1383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1383)、`:1406`：`nonlocal` 必须找最近“实际绑定该名字”的函数，不能只找最近函数。**

   ```python
   def outer():
       P = "/t" + "mp/cls-exam/x"
       def middle():
           def inner():
               nonlocal P
               P = "/etc/passwd"
           inner()
       middle()
       return P
   ```

   `outer()` 实际返回 `/etc/passwd`；记录却被搬到没有绑定 `P` 的 `middle`，全部漏检。给 `middle` 再加 `nonlocal P` 仍漏：前序遍历已经处理完 `middle`，随后搬入的记录没有继续归并。绑定查找还必须包括参数。

3. **[test_skill_portability_lint.py:1492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1492)：heredoc 必须按命令、fd 和重定向顺序归属，不能取整行最后一份。**

   ```sh
   python3 - 3<<'A' <<'B' <&3
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   A
   X=0
   B
   ```

   Python 实际读取 A，提取器却只返回 B 的 `X=0`。启动行换成以下任一种，也同样漏检：

   ```sh
   python3 - <<'A' 3<<'B'
   python3 - <<'A' | cat <<'B'
   ```

   反向问题：`python3 - <<'A' </dev/null` 不执行 A，却被登记。**fd 示例已验证属于相对 `b001cf83` 的回归。**

4. **[test_skill_portability_lint.py:1433](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1433)、`:1445`、`:1478`：解释器参数及命令边界识别会漏掉真实执行区。**

   - `python3 -W ignore <<'A'`：把 `ignore` 误认为脚本文件名。
   - `'python3' - <<'A'`：没有归一化可执行词的引号。
   - 下例只收第一段 `pass`，遗漏第二个 Python 命令：

     ```sh
     python3 -c 'pass'; python3 -c 'P="/t"+"mp/cls-exam/x"; P="/etc/passwd"'
     ```

   合法的 `-c'字面脚本'` 连写也遗漏。前两项已验证为 **`b001cf83` 能抓、`e22c6d27` 漏掉**；这些输入不涉及脚本变量数据流。

5. **[test_skill_portability_lint.py:1480](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1480)、`:1495`：原文中的假 heredoc 标记会吞掉后续真正执行区。**

   ```sh
   # <<'NO'
   python3 - <<'A'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   A
   ```

   `_python_regions()` 返回 `[]`。第一行换成 `echo '<<NO'` 也一样：词法分析使用了去注释版本，heredoc 扫描却重新使用未保护的原文。这是既存缺口。

6. **[test_skill_portability_lint.py:1176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1176)、`:1192`：显式命名空间写入和 `exec` 没有进入“不支持则登记”。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   globals()["P"] = "/etc/passwd"
   ```

   实际 `P` 被覆盖，全部判据静默。模块级 `locals()["P"] = …`、`globals().update(P=…)`、`exec('P = "/etc/passwd"')` 同样遗漏。

   本卡至少应登记这些直接可见的机制，无需实现任意动态代码分析。另一个写入覆盖缺口是 `type P = int`：它确实替换了绑定，却未进入 `_assignments()`；未另计 HIGH。

**MEDIUM：2 条。**

1. **[test_skill_portability_lint.py:1127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1127)、`:1394`：定义处表达式被重复归入新作用域，再错误套用其 `global` 声明。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   def outer():
       def f(x=(P := "/etc/passwd")):
           global P
           pass
   outer()
   ```

   默认参数写入的是 `outer` 的局部 `P`，模块 `P` 始终合规，却被报告为覆盖。class 基类表达式也有同类问题。内存对照确认这是**既存误报，本轮尚未消除**。

2. **[test_skill_portability_lint.py:1465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1465)：整块能被 Python AST 解析，不代表它是同一个 Python 执行区。**

   `cat <<'A'` 恰好可解析成左移表达式，因此普通 cat heredoc 中的两次赋值会被误报为执行中的覆盖。两个 `python3 <<'A'`／`python3 <<'B'` 独立进程也可能被整块 AST 合并，产生跨进程重赋值误报。

**LOW：1 条。**

- **[test_skill_portability_lint.py:1226](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1226)、`:1244`、`:1256`、`:1266`：旧控制流 helper 整组成为死代码。** `_branch_index()`、`_branch_path()`、`_in_loop()`、`_mutually_exclusive()` 已无存活调用；修改它们不会改变任何判据结果。

其余问题逐项结论：

| 维度 | 结果 |
|---|---|
| 嵌套函数／class 体内 `global` | **未发现漏检**。声明后的赋值就是全局赋值，不同时构成独立局部绑定。 |
| `*args`、`**kwargs` 注解 | 枚举确实漏列，但**未发现当前 Python 3.14.4 下的有效漏检反例**；海象注解会被编译器拒绝，不能只凭 AST 可解析认定有效。 |
| PEP 695 参数、`ast.arg.type_comment` | 除上述 `type` 名字绑定外，**未发现有效新增问题**；`type_comment` 不是执行表达式。 |
| `del P` 后普通重绑 | **未发现漏检**。单独删除未登记，但未证明产生越界路径。 |
| `{ python3 - <<'A'; } \| cat`、单独 `python3 <<'A'`、单独 `exec 3<<A` | **未发现所问具体形态的漏检或错误执行区认定**；多进程组合仍受 MEDIUM-2 影响。 |
| 整行结束标记、`<<-`、连字符定界符、同命令两个 stdin heredoc | 所测整改形态**未发现残留**。 |
| 本轮四项 URL 整改、交接常量、start-exam-board 最小 diff | **未发现新增问题**。 |
| 配对性能 | **未发现二次退化**；合成输入规模翻倍时完整动态判据耗时约翻倍。未复测禁读真实树。 |

**两条保守面可以保留，但不能统一解释为“最终值必然取决于运行时”。** `try` 的异常分支直接重新抛出、`else` 合规覆盖时，凡正常离开结构的路径都合规；失败 guard 后有无条件合规 `case _`，也能保证最终值。当前登记它们属于保守误报。常见的“两支都合规的完整 if/else”和固定非空循环也会被多报。**未发现必须为本卡实现完整可达性分析的理由**，有限消噪可以另立卡。

**分界应以“能否静默穿过当前门”为准。** 上述普通执行关系、绑定归属、字面 shell 命令及显式反射机制，属于本卡应修复或触发未知登记的范围。跨 fence／进程数据流、动态 `SCRIPT` 内容、任意 `sys.settrace`／外部装饰器行为、完整 shell／CommonMark 容器解析可以另立卡；但跨行引号、`_shell_words`、容器栈不能仅凭列入清单就视为已兜住——第十条看不到拆成 `"/t"+"mp"` 的路径。

**本轮 BLOCKER 0 条，HIGH 6 条。**
