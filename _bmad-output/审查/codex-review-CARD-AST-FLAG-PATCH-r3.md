绑定 **`a03af47cb35560f62920e5bb9c547f16b9e7bd9e`**：**BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2，建议整改后再复核。**

round-2 存档中的 **11 个输入均已独立复现为预期结果**；但表外输入仍暴露整改残留和新增回归。

1. **HIGH — round-2 HIGH-4 未完全修好：`ast.walk()` 中的 `continue` 不会剪掉作用域子树。**

   [lifespan_isolation_negative_control.py:581](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:581)

   ```python
   import threading as mod
   from app.main import app
   from fastapi.testclient import TestClient

   if True:
       def unrelated():
           setattr = None

   setattr(mod, "client", TestClient(app))
   with mod.client:
       pass
   ```

   **复现：**现版返回 CLEAN；删除整个 `if` 块后恢复 CAUGHT。

   `unrelated` 内的局部赋值仍被遍历到，导致 `_module_binds_name=True`、属性写路径为空。实际模块调用仍使用内建 `setattr`。条件块内的 class 局部赋值也能复现。原来的直接顶层函数输入已修，**同类跨作用域污染仍在**。

2. **HIGH — 新增 `except`／pattern 绑定识别引入漏放：一次绑定关闭整个模块，忽略调用时的实际绑定。**

   [lifespan_isolation_negative_control.py:568](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:568)，消费点 `:625–629`。

   将上一例的 `if` 块替换为：

   ```python
   try:
       raise ValueError()
   except ValueError as setattr:
       pass
   ```

   **复现：**`6564fc09` 判 CAUGHT，`a03af47c` 判 CLEAN。

   异常处理结束后，`setattr` 捕获名已被清除，后面的调用恢复使用内建函数；已用不导入项目的独立代码确认。Python 明确规定异常捕获目标在退出时删除。[官方规则](https://docs.python.org/3/reference/compound_stmts.html#except-clause)

   同一全模块开关还会被这些情况误触发：

   - `if TYPE_CHECKING: setattr = None`：运行时没有发生绑定。
   - 真正的 `match ... case setattr` 写在危险调用**之后**：后来的捕获反而让先前的写入逃过检测。

   因此，四种捕获确实是真绑定，但不能据此证明模块中每个调用点都被遮蔽。

3. **MEDIUM — 收窄扫描新增误报：顶层条件块中的真实 `def`／import 绑定反而漏收。**

   [lifespan_isolation_negative_control.py:572](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:572)，关联 `:577–584`。

   ```python
   import threading as mod
   from fastapi.testclient import TestClient

   if True:
       def setattr(obj, name, value):
           return getattr(obj, name)

   setattr(mod, "_active_limbo_lock", None)
   with mod._active_limbo_lock:
       pass
   ```

   **复现：**`6564fc09` 判 CLEAN，现版判违规；现版 `_module_binds_name=False`。

   这里调用只读取锁。`FunctionDef.name` 和 import alias 的识别仅处理 `tree.body` 直接成员，进入条件块后没有对应处理。**round-1 MEDIUM 的直接顶层输入已修，但同类真实遮蔽在条件块中重新误判。**

4. **LOW — 第 11 个变异不能保证“指定的那一条”变红。**

   [negctl.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/negctl.py:124)，目标定义在 `:86`。

   **复现：**静态用 `want_label in label` 匹配，`验伪锚 R2-M5` 同时命中 **M5、M5b**。

   即使只有 M5b 红、M5 没红，判据仍通过，并报告“指定 M5 红、连带红 0”。应使用唯一 ID 或完整标签，并验证唯一匹配。当前删除四类绑定的变异机制能够影响两例；这里发现的是**指定目标证明不唯一**，不是断言该变异无效。

5. **LOW — round-2 LOW-7 的具体 territory 引用已修，但索引完整性仍未闭合。**

   [README.md:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/README.md:40)

   **复现：**索引引用 `fixpoint-rounds-instrument-…085801.txt`，提交树中不存在；实际名称为 `fixpoint-rounds-instrument-20260917T085801.txt`。

   虽然它是 VOID 过程件，仍违反 `:47–49` 声明的逐文件存在性检查；只检查 `<…ts…>` 捕获不到这种省略号引用。

其余重点核对结果：

| 核对项 | 独立结论 |
|---|---|
| HIGH-1／HIGH-2 的 lambda 整改 | 指定失效路径已修；更深默认值、tuple、def／async def 组合未复现新回归 |
| 递归终止 | 正常 `ast.parse` 树上严格进入后代，无循环路径 |
| “产出不含 lambda” | **产出节点自身**不是 Lambda；Tuple 等产出的子树仍可能含 Lambda，由调用方继续处理 |
| 注解完整性 | Python 3.11.15 下，五类参数注解加返回注解共 6 条 yield，walker 与外层字节码计数一致；async 组合一致 |
| class 外层表达式 | bases、metaclass keyword 已覆盖；实测 walker 与外层字节码均计 2 条 yield |
| Python 3.14 | 未复现本次补收造成的新误判；合法注解内 lambda 体的 yield 被正确排除。[注解作用域规则](https://docs.python.org/3/reference/executionmodel.html#annotation-scopes) |
| 两条注解负控 | 当前确因 **TestClient 未隔离**而红，不是 SyntaxError 空门 |
| 两条新增 must-pass | CLEAN 正确；except 样例的处理分支本身不可达 |
| 已登记局部同名残留 | 所述形态确为多收写路径、误撤 C4，方向是 fail-closed；不能推广到上述全模块开关问题 |
| 三条原始盲区 | 原始锚均仍 CAUGHT；但 `setattr` 修复仍存在上述漏放 |
| 59／31 与扫描 | 独立复现表内零漏报、零误报；改前与现版完整扫描均 **401 文件、空违规集** |
| 单测证据 | 1185 行完整，含摘要和 `rc=1`；提取的 **64 条失败／错误**与两份 nodeids 一致，round-2 MEDIUM-6 已修 |
| 公共符号、地盘 | 既有公共符号保留；`5f9fd306 → a03af47c` 确实只有地盘回执 |

另需收窄“根位置与 `B14_BASE` 逐字同”的声明：

```python
lambda cb=lambda x=(a := 1): x: cb
```

以此 lambda 为 `_own_exprs` 根输入，基线收 `[]`，现版收 `['a']`。这是符合定义时求值的预期变化，**不算代码缺陷**，但普遍等价的声明不成立。

11 个变异的源码替换锚均唯一；前 10 个目标标签也唯一，静态未发现靠无关机制变红。控制组为空只支持 **90 个固定样例**的对照，不能证明目标唯一或整类语法无回归。

全程只读，未运行变异 harness、未执行含项目导入的危险样例、未连接 7691／7687、未写文件；未评价两项明确排除范围。
