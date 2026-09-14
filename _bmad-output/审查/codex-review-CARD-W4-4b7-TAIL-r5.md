> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-4b7-TAIL round-5（末轮，D-15 上限）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4b7-TAIL-r5.md)"`
> 审查绑定: `6e4fedc5`（审前审后 HEAD 均为此，Codex 正文第 3 段自证）。其后仅一个 D-32 纯 docstring commit `a008882e`（剥 docstring 后 AST 逐字节相同，不占轮次）⇒ 本轮仍绑最终代码态
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:4） / `model: gpt-6-astra`（.stderr:7） / `reasoning effort: ultra`（.stderr:11）

---

**本轮 BLOCKER：0；HIGH：0。发现 1 项 MEDIUM、2 项 LOW。** 扩大的拒绝面仍遗漏一种 AST 可见的延迟求值体，残留文案也未完全清除；未发现本轮引入的新回归。

审查前后 HEAD 均为 `6e4fedc5555223ed73a3aae1291a650e91669715`，两份源码相对该提交无差异。全程只读，未连接数据库。

**MEDIUM-1：拒绝表遗漏 `ast.TypeAlias`，仍可造成两个顺序门假绿。**

位置：[test_live_port_guard_contract.py:1365](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1365)，同文件 `:1302-1317`、`:1833-1841`、`:1869-1882`。

一句话复现：把 hook、注册调用写进两个 `type` 别名的右侧，首次预检之后才读取其 `__value__`。

```python
def install():
    type H = _install_audit_hook()
    type R = register_final_accounting()
    assert_neo4j_target_blocked()
    H.__value__
    R.__value__
```

- 项目解释器 **Python 3.14.4** 下，原拒绝函数实测放行。
- `TypeAlias.value` 内的两个 `Call` 完全可见；按当前收集与比较实现，下标为 **0／1／2，两个门均满足断言**。
- 用内置 `print` 独立验证求值顺序，实际为 **precheck → hook → register**。

这属于本轮承诺覆盖的“可见延迟执行体”。`type` 别名自 Python 3.12 起惰性求值，读取 `__value__` 才求值；不是已登记的字符串或外部 helper 漏面。[Python 官方说明](https://docs.python.org/3.12/reference/executionmodel.html#lazy-evaluation)

**LOW-1：文案清理未完成，“恰好四类”也仍不精确。**

位置：[test_live_port_guard_contract.py:1296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1296)，同文件 `:1239-1248`、`:1265`、`:1300`。

一句话复现：分别检查 `@identity` 函数、带默认参数的无装饰器函数，以及含调用的返回类型注解。

- `:1297` 仍断言“带装饰器的 body 在定义点执行”，与 `:1261-1263` 新增的“保守计入”解释矛盾。
- `:1300` 仍称“不带装饰器的 def 不贡献任何调用”，但 `:1294` 会计入默认参数调用。
- `:1291-1301` 还跳过 `returns`、`type_params`，并同时处理 `AsyncFunctionDef`；因此“恰好四类／其余一律”未完整描述实现。例如 `def f() -> annotation_call(): pass` 不收该调用，而参数注解中的调用会收。

**新 docstring 的两句核心更正核对通过**：`:1261-1263` 的“带装饰器保守计入”“装饰器表达式与默认参数计入”符合 `:1291-1299`。`local_funcs`、`expand_call`、调用点展开及在途集合等旧机制说明，也已删除。

**LOW-2：总验证存档的数量与“全部翻红”自述不符。**

位置：[codex-all-rounds-repro-verify-r5-20260914T214830.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/codex-all-rounds-repro-verify-r5-20260914T214830.txt:2)。

一句话复现：逐行计数复现标签，再对照 round-4 的原始 `type()` 反例。

实际是 **16 条复现标签＋2 条干净形态**，不是“18＋2”；另外三条登记漏面确实打印为绿。

round-4 [报告 :44](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/codex-review-CARD-W4-4b7-TAIL-r4.md:44) 的原例：

```python
type("Early", (), {"__init__": assert_neo4j_target_blocked})()
```

没有 `ClassDef`。本轮拒绝函数对此仍实测放行，且总验证档没有对应翻红条目。因此，“原 `type()` 动态绑定例已因 class 体而翻红”不能成立；将其登记为剩余边界的 docstring 才是准确口径。

对其余指定问题，核对结果如下：

| 项目 | 结论与位置 |
|---|---|
| async 四类推导式／生成器表达式 | **核对通过**。仍是原四种节点，异步标记不影响拒绝；`:1371`。 |
| `match` guard、`NamedExpr` 内 lambda | **核对通过**。`ast.walk` 会进入表达式并找到 `Lambda`；`:1362-1370`。普通 guard 自身不是延迟体。 |
| `global`／`nonlocal` 配合 lambda 赋值 | **核对通过**。声明不阻止遍历赋值右侧，均拒绝；`:1362-1370`。 |
| 装饰器表达式、非字符串注解内 lambda | **核对通过**。嵌套 `Lambda` 可见，均拒绝。 |
| 字符串前向引用 | 收到的是 `Constant(str)`，不会把字符串内容再次解析成 `Lambda`／`Call`，属于不可见内容。 |
| 三个 flag 的空串及数字短 SHA | **核对通过**。[跑器 :48-60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:48) 共用检查。9 条独立参数探针确认三个空串均 rc=2；`46e7bf77`、`6e4fedc5`、`485a1f89` 正常接受。 |

两个顺序门的 claim **收窄方向核对通过，但仍应按更精确的含义理解**：它们证明的是“按指定规则剪枝后，三个名字首次出现的**顶层语句下标**满足 `hook < register < precheck`”。位置为同一测试文件 `:1302-1307`、`:1833-1841`、`:1869-1882`。其中也接受任意 `ast.Attribute` 的末级名字；没有验证调用对象身份、分支之间的实际执行关系或同一语句内部的顺序。

除已登记的 helper、partial、字符串、动态绑定外，再列一项剩余边界：函数内 `h: _install_audit_hook()` 的注解表达式**不执行**，当前遍历仍会计入其调用。它不是延迟体，故未另算本轮 MEDIUM。

⑤ 的回归核对结果：

- **核对通过**：限定完整 diff 确认 `_indirect_self_method_calls`（`:1082`）、seam 两门、源码导出白名单及相等漂移钉、前三类剪枝均未改。
- **核对通过**：`_reachable_prefix`（`:1217-1229`）独立覆盖四种终结语句，保留终结语句自身，只截掉后缀，不改变保留语句的下标。
- **核对通过**：[_publish_ledger :1408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1408) 所在文件与 round-4 逐字相同；对比前提 `46e7bf77`，去除 docstring 后 AST 均为 **1437 字符、完全相同**。
- **存档核对通过**：[预检档 :11-35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/r5-precheck-20260914T214842.txt:11) 的 152 passed、七个定向节点，以及三份负控的 before 绿／after 指定原因红／clean 绿。重新计算的两份源码 SHA256 与三份负控记录一致。

已登记的 summary 来源边界仍存在，未重复计为新增问题：后置伪造区段或只有伪造区段仍可接受；无标题、最后区段为空及“伪造在前、真实在后”均拒绝。真实 `install()` 的 `4/5/6` 和 pytest 结果属于**存档核对**，本轮没有运行完整 pytest 或会修改工作树的负控跑器。


