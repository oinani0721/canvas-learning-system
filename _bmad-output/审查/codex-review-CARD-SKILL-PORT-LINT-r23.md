**新的三分法仍不成立，不能据其未命中判定安全。** 已复现条件写入被跳过、延迟执行、绑定归属错误和执行区漏提取。

复核绑定 **`b001cf83fefd869b0594b2e0442fa5c35e060242`**；收尾时被审文件仍对应提交 blob `40966c7c47ab63fe8884ccfb47af15800232cbfe`。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**BLOCKER：未发现。**

**HIGH：5 条，按根因归并。**

**HIGH-1 — [test_skill_portability_lint.py:1274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1274)：既非循环、又非互斥的两处写入，仍不一定是必然执行的直线覆盖。**

```python
P = "/etc/passwd"
if False:
    P = "/t" + "mp/cls-exam/x"
```

实际最终值为 `/etc/passwd`，`dynamic_tmp_join_lines()` 却返回 `[]`。把 `False` 改为 `True` 是安全对照，**九计数和全部附加正文判据，包括第十条指纹，完全相同**。

生成器延迟执行同样打穿源码顺序：

```python
g = ((P := "/etc/passwd") for _ in (1,))
P = "/t" + "mp/cls-exam/x"
next(g)
```

全部判据仍为空。这里缺的是“写入何时执行、后写是否必经”，不是再补一种循环节点。

三分法也有反向误报，归入本条不重复计级：循环结束后无条件赋合规值、`try.body` 写坏值后 `else` 写合规值，以及失败 guard 写坏值后下一 case 写合规值，均已实测报红。

**HIGH-2 — [test_skill_portability_lint.py:1302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1302)：`nonlocal` 被统一迁入模块，漏掉实际外层函数绑定。**

```python
def outer():
    P = "/t" + "mp/cls-exam/x"
    def inner():
        nonlocal P
        P = "/etc/passwd"
    inner()
    return P
outer()
```

合规写入留在 `outer`，越界写入被放进 module，无法配对；全部正文判据为空。反方向也会把修改独立外层局部变量误报成修改模块变量。

`nonlocal` 必须解析到最近的适用外层函数绑定，不能与 `global` 共用迁移目的地。

**HIGH-3 — [test_skill_portability_lint.py:1110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1110)：截断整个嵌套作用域节点，把实际在外层求值的默认参数、基类表达式划进内层，是新回归。**

```python
P = "/t" + "mp/cls-exam/x"
def f(x=(P := "/etc/passwd")):
    pass
```

定义函数时模块 `P` 已被覆盖，判据却全部为空；海象目标改成 `Q` 的安全对照与其完全同判。

`lambda` 默认参数、`class C((P := object)):` 也已复现。不能把“函数体建立新作用域”推广成“整个 `FunctionDef` 的子节点都属于新作用域”。

**HIGH-4 — [test_skill_portability_lint.py:1304](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1304)：迁移 `global` 写入只合并名字，丢失调用时序和原始父链。**

```python
def f():
    global P
    P = "/etc/passwd"
P = "/t" + "mp/cls-exam/x"
f()
```

源码靠前的函数体实际最后执行，全部正文判据仍为空。

另一个独立复现是：函数内声明 `global P`，执行本轮已有的“首轮合规、次轮越界并 break”循环。迁回 module 后，两条记录的 `_in_loop()` 都变成 `False`、`_branch_path()` 都变成 `()`，于是漏检；去掉 `global` 后相同循环可以命中。

因此，**普通局部作用域的父表未发现缺边；搬运记录后继续使用模块父表，确实会缺边。**

**HIGH-5 — [test_skill_portability_lint.py:1344](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1344)：执行区提取没有遵循 heredoc 的定界、重定向和接收命令语义，也漏掉明确的 Python `-c` 字面脚本。**

例如：

```sh
python3 - <<'A' <<'B'
X = 0
A
P = "/t" + "mp/cls-exam/x"
P = "/etc/passwd"
B
```

实际 stdin 来自 **B**，当前只提取 A，全部正文判据为空。另已复现：

- **`:1350` 的 `.strip()` 提前闭区**：结束标记为 `PY` 时，正文中的 `PY ` 不应结束 heredoc。先定义 `PY=0`，让该行成为合法 Python 表达式，即可把后续越界赋值藏出执行区。
- **`:1352` 的 `dedent()` 不等于 `<<-`**：后者逐行剥前导 tab；一行带 tab、一行不带时，当前可能解析失败并丢掉整个区。
- **`:1318` 不接受合法的 `<<'PY-END'`**，同形重赋值漏检。
- `python3 -c 'P="/t"+"mp/cls-exam/x"; P="/etc/passwd"'` 返回空执行区，全部正文判据为空。
- 反方向，`cat > /dev/null <<'PY'` 或 `python3 -c 'pass' <<'PY'` 的输入被误当成执行的 Python，产生重赋值误报。

同一进程也不能自动串联：`python3 - <<A <<B` 是最后一次 stdin 重定向生效；`python3 -c 'pass' <<A` 中 A 只是未读取的数据。只有实际读取并执行到相同命名空间，才形成共享执行关系。

**MEDIUM：4 条。**

- **MEDIUM-1 — [test_skill_portability_lint.py:2155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2155)：新增段首锚漏掉带合法前缀的 `printf -v`。**  
  `builtin printf -v CLS_BACKEND_URL %s ""; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"` 返回 `False`，裸 `printf` 返回 `True`；`{ printf …; }`、`then printf …` 同漏。这些确实清空配置，属于新回归。

- **MEDIUM-2 — [test_skill_portability_lint.py:2383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2383)：`env -u` 的新正则消费开引号，却未消费闭引号。**  
  `env -u "CLS_BACKEND_URL" bash -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` 返回 `False`，去掉变量名引号返回 `True`；这是普通整体引用的新回归。此外 `bash -cl` 仍漏，不能只覆盖 `-lc`。

- **MEDIUM-3 — [test_skill_portability_lint.py:2338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2338)：只检查紧邻展开的 `@`，仍不足以判断主机受控。**  
  `curl "${CLS_BACKEND_URL:-http://localhost:8011}":pw@localhost/x` 返回 `False`；配置为 `http://remote.example` 时，实际 URL 主机仍为 `localhost`。未引用的 `\@localhost/x` 也漏，涉及顶层反斜杠应被 shell 去除的语义。

- **MEDIUM-4 — [test_skill_portability_lint.py:2230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2230)：展开层中双引号内的字面 `(` 被压入结构栈，造成新误报。**  
  `echo "$(printf %s "(")"; # unset CLS_BACKEND_URL` 返回 `True`，实际 `unset` 属于注释；把 `(` 换成 `x` 返回 `False`。仅在内存撤掉新增裸括号跟踪逻辑，注释识别即恢复。

前三条的安全／坏对照均保持九计数相等，URL 判据均为 `[] → []`，其余正文判据也未兜住。

**LOW：1 条。**

- **LOW-1 — [test_skill_portability_lint.py:1267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1267)：两两配对确有二次退化，并重复计算祖先链、存储重复命中。**  
  合成输入中，同名 tmp／other 写入各为 100、200、400、800 条时，纯重赋值检查约耗时 **10、39、158、597 ms**，倍增接近四倍；`hits` 最坏空间也为 `O(tmp×other)`。未读取真实正文，不能据此认定当前树超时，也未复核所报冷／暖耗时。

其余指定维度：

| 维度 | 结论 |
|---|---|
| 普通分号语句的列顺序 | **未发现问题。** |
| 表达式内 `col_offset` 是否等于执行顺序 | **不等于。** 赋值先求右侧；推导式的迭代／过滤先于元素表达式。所测反例已被动态祖先检查命中，未另发现独立全门漏检。 |
| 普通 `if/else`、`elif` 的 body 分叉编码 | **未发现独立结构错误。** 条件求值及是否必经的问题见 HIGH-1。 |
| `try/else`、`match` guard | **归类不对。** try body 与 else 可顺序执行；失败 guard 的副作用可保留到下一 case，不能把整个 case 都视为互斥。 |
| `try/finally`、`with`、`continue` | 必须考虑异常、抑制异常和提前退出；“源码在后”不能证明合规写入必执行。并非这些结构总会倒转顺序。 |
| 生成器、`await`、递归／回调 | 存在延迟执行或再次进入函数的情况，不能继续用定义位置排序；已直接复现生成器和普通 global 调用漏检。 |
| `_sh_strip_quotes()` 不动点收敛 | **未发现不收敛。** 每次变化都严格缩短字符串。未找到额外剥引号造成的独立有效 URL 反例；转义缺口见 MEDIUM-3。 |
| `_ident_text()` 身份编码 | **未发现本轮新增碰撞。** |
| 已修的顶层转义、反引号层、`-c` 后第一词边界 | 对现有回归样本**未发现独立残留问题**；新增邻接形态见上述 MEDIUM。 |
| 交接常量 | 纯函数检查返回 `[]`，**未发现问题**。 |

三条新增回归测试函数直接在内存调用均通过，但没有覆盖上述反例。另需限定“逐处”的表述：当前仍按空白 token 判定，尚未实现每个 `8011` occurrence 的独立绑定；本轮不额外计一条缺陷。

**残余清单仍不完整。** 本轮确实补上了普通局部作用域隔离、多种写入目标、部分循环／分支形态、普通 heredoc，以及所列 shell 和身份编码修点；还缺的是本报告证明的绑定归属、必经覆盖、延迟执行、父链来源和执行区词法问题。

本卡与另立卡的分界应是：

- **本卡修完**：上述已宣称覆盖的确定性语法和新回归。不能把 `nonlocal`、默认参数求值、普通引用的 `env -u`、heredoc 定界等归入“脚本变量数据流”后结卡。暂不支持的执行关系应明确触发登记，不能因源码顺序或解析失败静默放行。
- **可以另立卡**：一般间接调用、完整异步调度、跨进程或动态 `exec` 数据流，以及完整 Markdown 容器解析。现有跨物理行引号、复杂 `_shell_words` 边界可以保留为明确限制；但需注明漏检方向及兜底是否覆盖。你提到的“四条容器双向反例”在本轮限定材料中没有完整对应样本，因此不声称逐条重验或已完整闭合。

**本轮 BLOCKER 0 条，HIGH 5 条。**
