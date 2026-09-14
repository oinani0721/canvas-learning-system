> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-4b7-TAIL round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4b7-TAIL-r4.md)"`
> 审查绑定: `485a1f89`（审前审后 HEAD 均为此，Codex 正文第 3 段自证）。本轮结论作出后按其 MEDIUM-1 与 LOW-1/2 整改，新 HEAD `6e4fedc5` 已另送 round-5（末轮）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `reasoning effort: ultra`（.stderr:9）

---

**本轮 BLOCKER：0；HIGH：0。发现 1 项 MEDIUM、3 项 LOW。** “遇局部函数即拒绝”确实收紧了两个顺序门，但**没有清空假绿面**。

审查前后 HEAD 均为 `485a1f894a28a9c368168cf8fe1728d85b630b36`，两份源码无工作树差异。执行了内存 AST、事件顺序和跑器文本探针；未修改文件、运行完整负控跑器或连接数据库。

**MEDIUM-1：没有局部 `def`，仍可把未执行的函数体记为提前调用，造成双假绿。**

位置：[test_live_port_guard_contract.py:1395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1395)，同文件 `:1332-1341`、`:1852-1860`、`:1888-1901`。

一句话复现：用两个 `lambda` 包住 hook／注册，在首次预检之后才调用它们。

```python
def install():
    h = lambda: _install_audit_hook()
    r = lambda: register_final_accounting()
    assert_neo4j_target_blocked()
    h()
    r()
```

独立实测：

- `_local_func_defs == {}`，拒绝断言不触发。
- hook／register／precheck 下标为 **`0 / 1 / 2`，两个门均绿**。
- 实际事件为 **`precheck → hook → register`**。

你指定的其他构造也逐项核了：

| 构造 | 独立复核结果 |
|---|---|
| 生成器表达式只创建、不迭代 | 可双假绿：两个生成器分别包含 hook／注册，随后预检；下标 `0/1/2`，实际只有预检。 |
| 空列表推导式 | 可双假绿：hook／注册放进 `for _ in ()`；同样下标 `0/1/2`，实际只有预检。 |
| 模块级 helper | 可双假绿：`early()` 内执行提前预检，随后三个直接调用；下标 `1/2/3`，漏掉第一次预检。 |
| `partial(assert_neo4j_target_blocked)()` | 放在三个直接调用前，仍读为 `1/2/3`，双假绿。 |
| `exec`／`eval` 字符串调用预检 | 同上；字符串内调用不会被解析。 |
| `type()` 动态绑定方法 | `type("Early", (), {"__init__": assert_neo4j_target_blocked})()` 可隐藏提前预检，双假绿。 |
| 普通 class 内显式 `def` 方法 | **能够收得到，核对通过**；裸 `ast.walk` 会进入类体，拒绝断言生效。 |
| class 内直接绑定模块函数为方法 | 没有 `def`，仍可隐藏提前预检。 |

这些是**剩余漏面，不是本轮新引入的假绿**。对同一输入，本轮收紧方向成立：有局部定义直接拒绝；没有局部定义时，旧版空函数表的展开本来就不起作用。不能由此进一步推出“无局部定义 ⇒ 顺序判断可靠”。

**LOW-1：语义说明仍残留已删除的机制，并错误保证模块级包装。**

位置：[test_live_port_guard_contract.py:1266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1266)，同文件 `:1287-1292`、`:1324`、`:1366`、`:1382-1391`。

一句话复现：对照只有 `node` 参数的当前实现，文档仍要求传 `local_funcs`、调用点展开、递归在途集合及 `local_funcs=None` 模式，注释还引用已删除的 `expand_call`。

此外：

- `:1259`“只数定义点之外的调用”不准确：`:1316-1323` 仍计入装饰器表达式、默认参数调用和带装饰器函数体。
- 独立探针 `@identity` 装饰的 `def helper(): target()` 返回 `['target']`；实际 identity 装饰器可以完全不执行该函数体。因此应写“保守计入”，不能写成“定义时确实执行”。
- `:1366`“模块级的调用关系顺序门本来就数得对”，已被上面的模块级 helper 反例证伪。

两个正式顺序门会先拒绝这些局部定义，因此装饰器文案问题没有另算一个顺序门漏洞。

**LOW-2：`--prereq ''` 仍能通过参数解析，前提绑定变成 index。**

位置：[negctl_w4_gates.sh:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:49)，同文件 `:56`、`:72`、`:241`。

一句话复现：抽取原解析片段执行 `--gate whitelist --prereq '' --help`，实测 **rc=0**；不带 help 也能得到空的 `PREREQ`。

随后 `git show "$PREREQ:$TEST_REL"` 会成为 `git show ':路径'`，读取 index，不能代表指定的前提提交。`--gate ''`、`--phase ''` 均会拒绝。这是剩余取值边界，**不推翻裸旗标缺值修复通过**。

**LOW-3：最后一个 summary 仍只有文本位置约束，没有来源保证。**

位置：[negctl_w4_gates.sh:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:275)，同文件 `:287-292`。

一句话复现：真实 summary 后追加完整伪造区段，或者没有真实 summary、只保留捕获输出中的伪造区段，原提取器及节点关键词检查仍接受。

这是**文本探针确认的剩余边界**，没有声称当前 pytest 实际产生了这种输出。原 round-3 的“伪造在前、真实在后”复现已正确拒绝。

**其余问题核对结果：**

| 项目 | 结论及位置 |
|---|---|
| ①(b) 是否漏加前置断言 | **核对通过**。全文件 `_live_called_names` 实际调用仅 `:1853`、`:1889`，分别先经过 `:1850`、`:1886`。未发现第三处同类顺序下标判据。 |
| ①(c) 合法重构假红 | 未调用的普通 helper、恒假分支内的 helper、无关局部类方法都会拒绝。若明确约束 `install()` 禁止局部定义，这可作为人工复核触发条件；不能解释为真实顺序错误。 |
| 顶层下标粒度 | 正确三调用放在同一个 `if True` 或元组表达式中，下标都是 `0`，仍会假红；这是既有边界。 |
| 前三类剪枝 | **核对通过**，`:1203-1229`、`:1303-1314`、`:1335-1336`。20 个独立剪枝／前置条件样本通过，涵盖真假分支、终结语句、handler／finally、with 后继和 match。 |
| `_reachable_prefix` | **核对通过**，`:1224-1229` 只截断后缀，保留终结语句自身及剩余语句的原下标。 |
| 无 summary 标题 | **核对通过**。跑器 `:275-278` 输出空串，awk 自身 rc=0，但 `:287-292` 关键词检查失败；方向是拒绝／可能假红。 |
| 最后 summary 为空 | **核对通过**。`n=0` 后不会输出旧 buffer；同样拒绝，不会复用前段假绿。 |
| 三个裸旗标缺值 | **核对通过**。跑器 `:54-56` 全部改到调用方；独立实测均为 `missing value for <flag>`、rc=2。下一旗标占值也均拒绝。 |
| 间接调用、seam、白名单漂移钉 | **核对通过，未见本轮回归**。完整限定 diff 确认 `_indirect_self_method_calls`、seam 两门及白名单／相等断言未改；位置为 `:1082`、`:2039`、`:2109`、`:1487-1533`。行为结果属于存档核对。 |

**④ `_publish_ledger` 的三类说明：核对通过。**

[源码 :1449-1474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1449) 对应关系准确：

- 锁失败 `:1464-1465`、陈旧序号 `:1467-1469`：返回 `False`，本调用未调用写盘。
- `write_ledger` 在 `:1471` 抛出：此前 `:1470` 已推进发布序，文件状态未定。
- 非数序号在 `:1467` 比较抛出：尚未推进发布序，也未调用写盘；finally 释放锁。

普通同步控制流下未发现本轮仍说过头的地方。**纯 docstring 性质独立核对通过**：两版去除 docstring 后 AST 均为 1437 字符、完全相同。

最后明确证据强度：[12 个复现标签及两条对照存档](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/codex-all-rounds-repro-verify-20260914T213639.txt:2)、真实 `install()` 的 `{}`／`4/5/6`、152 passed、三份负控的节点红因和恢复哈希，均**存档核对通过**。总验证文件没有附实际输入脚本；真实 `install()` 源码也不在允许行段内，因此没有把它们表述为本轮独立重跑。


