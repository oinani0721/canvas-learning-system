> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-4b7-TAIL round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4b7-TAIL-r2.md)"`
> 审查绑定: `a307de45`（审前审后 HEAD 均为此，Codex 正文第 3 段自证）。本轮结论作出后按其 MEDIUM-1/2/3 整改，新 HEAD `c118e33e` 已另送 round-3
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `reasoning effort: ultra`（.stderr:9）

---

**本轮 BLOCKER：0；HIGH：0。发现 2 项新增 MEDIUM 回归，以及 1 项残留的 MEDIUM 假绿。原 round-1 指定复现已修复，但本轮不能判定为无回归。**

审查前后 HEAD 均为 `a307de45aa714c6258cbf4b8527da1a683e04fcc`，两份代码文件与该 SHA 一致。执行了内存 AST、调用顺序及文本判据探针；未修改仓库、运行项目 pytest／负控跑器或连接数据库。以下区分本次实测与存档核对。

**MEDIUM-1：跑器的 nodeid 身份检查变成恒真，属于新增回归。**

位置：[negctl_w4_gates.sh:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:193)，调用方同文件 `:204`、`:236`。

复现思路：令 `PYTEST_OUT` 为空或只含无关节点，再调用 `node_result_line "$node" FAILED`；实测没有输出，但退出码仍为 **0**，调用方进入成功分支。

`awk '$1 == n && $2 == w'` 的**字段表达式正确，退出状态用错了**：未匹配不等于 awk 执行失败。因此：

- before／clean 的验收退化为 `pytest rc == 0`，不能证明目标节点 PASSED。
- after 的逐节点 FAILED 检查同样失效；但仍受 `rc == 1` 和 summary 关键词检查约束，不能说整个 after 无条件通过。

**MEDIUM-2：把函数体调用记在定义位置，新增两个顺序门同时假绿。**

位置：[test_live_port_guard_contract.py:1328](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1328)，同文件 `:1843-1849`、`:1879-1887`。

复现思路：先定义负责 hook／注册的两个 helper，在第一次预检之后才调用它们。

```python
def install():
    def install_hook():
        _install_audit_hook()

    def install_final():
        register_final_accounting()

    assert_neo4j_target_blocked()
    install_hook()
    install_final()
    assert_neo4j_target_blocked()
```

独立 A/B 结果：

| 版本 | hook／register／首次 precheck 下标 | 两个顺序门 |
|---|---|---|
| round-1，按授权 diff 内存还原 | 缺失／缺失／2 | 均红 |
| round-2 | **0／1／2** | **均绿** |

合成片段实际执行顺序为 `precheck → hook → register → precheck`。

`expandable` 只证明名字被提及，却把未来执行的函数体提前归到 `def` 的下标。这也会新增假红：先定义预检 helper，随后正确执行 hook、注册、helper、直接预检，门仍把第一次预检记在定义处。

**这不是 `_reachable_prefix` 截断造成的重编号问题。**

**MEDIUM-3：作用域计算没有继续传播新发现的局部函数引用，仍能漏掉提前预检。**

位置：[test_live_port_guard_contract.py:1386](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1386)，同文件 `:1328`、`:1358`。

复现思路：在 `outer` 内定义并调用执行预检的 `inner`，再于下一条顶层语句调用 `outer()`，之后放 hook、注册和第二次预检。

实测：

```text
expandable = {'outer'}       # 缺 inner
hook / register / precheck = 2 / 3 / 4
两个顺序门均绿
真实执行：precheck → hook → register → precheck
```

首次逐语句扫描不会进入未被本子树提名的 `outer`；第二遍虽然展开 `outer`，此时发现的 `inner` 不在既定集合里，而 `expandable is not None` 又禁用了自足不动点。

甚至不需要嵌套定义：两个顶层局部函数 `first()` 调 `second()`，只有 `first` 在顶层被调用，也会漏掉 `second` 内的提前预检。**这是残留漏洞，不将它误报为本轮全部新引入。**

你特别指定的三类边界，独立核对如下：

| 形态 | 结论 |
|---|---|
| 嵌套函数 | 上述跨语句场景会漏。 |
| 同一条复合语句内完成全部“定义＋调用” | **可以展开**：预扫描的自足不动点能先把内外名字都纳入集合；实测 `expandable={'outer','inner'}`。不能笼统说传集合后一概不展开。 |
| `locals()["helper"]()` | 漏：没有 `Name("helper")`，可再次形成提前预检假绿。 |
| registry | 不能一概判漏。装饰器注册的函数体现在必展开；`registry[key]=helper` 也有 Name 引用。由 `locals()` 等反射取得对象、无装饰器及显式名字引用的路径仍可漏。 |
| 不同分支定义同名函数 | 简单函数体会一起展开，可能误红；**也可能漏**：首次 `local_funcs.setdefault`（`:1335`）只保留第一定义，第二定义内的嵌套函数可能进不了集合。实测仅将第一定义改名，就能使漏掉的内层预检重新被发现。 |

以上是有限识别面的具体列举，不要求本卡完成全称封闭证明。

**LOW-1：MEDIUM-1 原漏洞封住了，但确实新增合法临界区的假红。**

位置：[test_live_port_guard_contract.py:1147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1147)，同文件 `:1150`、`:1156-1158`、`:1179`。

复现：

```python
f = self.ledger
f = self._ledger_locked
f()
```

实际只调用白名单 helper；round-1 返回 `['_ledger_locked']`，round-2 返回 `['_ledger_locked', 'ledger']`，于是误红。

另有：

- `f=self.ledger; f=some_plain_value; f()`：仍报告 `ledger`。普通值若是安全 callable，就是假红；若不可调用，本来就会抛 `TypeError`。**直接覆盖不清绑定在 round-1 已存在。**
- `f=self.ledger; g=f; g=lambda:7; g()`：旧别名边不会失效，本轮新增传播后仍报告 `ledger`。
- 元组解包、`for` 目标、`with ... as f`：`:1136-1145` 没有收集这些绑定。三个独立探针均返回空列表，属于剩余漏面；若它们覆盖已有绑定，旧方法也不会被清除。

原两条覆盖复现则**核对通过**：普通后续覆盖、恒假分支内覆盖都返回 `['_ledger_locked','ledger']`；三级别名传播返回 `['ledger']`。基础 Assign／AnnAssign／海象／字面 getattr 识别也通过。

**LOW-2：summary 仍能被冒充，且关键词没有逐节点配对。**

位置：[negctl_w4_gates.sh:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:246)，同文件 `:249-253`。

复现思路：捕获输出提供 `FAILED other/<目标nodeid> - <关键词>`，真正 summary 中目标节点失败于另一原因；实测仍接受。

原因有三处：

- `^FAILED ` 从整份输出筛选，没有限定 short-summary 区段。
- `grep -F "$node "` 仍缺 nodeid 左边界。
- EXPECT_TEXTS 与 AFTER_NODES 做交叉搜索；两个 order 关键词可以由同一个节点提供，另一个节点失败于别处也能通过。

**关键词被截断不会静默放绿**：实测进入 `:257`，打印 FAIL 并返回失败；这是可能的假红。

关于输出格式，普通 `-v` 支持该字段假设；启用 xdist worker 后可能是 `[gw0] [100%] PASSED <nodeid>`，参数化 id 中的空格也会拆字段。仅 `-p xdist` 加载插件不等于启用 worker；`--tb` 通常改变回溯格式，不能据此断言结果行改变。官方示例中的 `-v` summary 仍可能截断。[pytest 输出文档](https://docs.pytest.org/en/stable/how-to/output.html)、[pytest 上游输出实现](https://raw.githubusercontent.com/pytest-dev/pytest/main/src/_pytest/terminal.py)、[xdist 文档](https://pytest-xdist.readthedocs.io/en/stable/)。这些是格式边界，未据此假定本机启用了相关选项。

**LOW-3：看门只杀一个 PID；隔离注释仍未同步。**

位置：[negctl_w4_gates.sh:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:172)，同文件 `:14`、`:105`、`:157`、`:219`。

复现思路：pytest 创建持续运行的子进程后超时，`kill -9 "$pid"` 不保证子进程一起终止。这里没有进程组清理，不能保证整棵进程树结束；本次未声称已经观察到实际孤儿进程。

你本轮承认“临时目录存备份、工作树接收变异”是正确的，但脚本 `:14` 仍写着“对照输入只写进临时副本”。恢复哈希一致也仍不证明运行期间隔离。

**LOW-4：原 `--help` 复现已修，但仍绕过参数值校验。**

位置：[negctl_w4_gates.sh:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:52)，同文件 `:44-45`、`:57-65`。

`--help --nonsense-arg` 实测 rc=2，**核对通过**。但 `--help --phase bogus`、`--help --gate bogus` 仍为 rc=0；`--phase --nonsense-arg --help` 也为 rc=0，因为未知开关先被当成参数值吞入。

**LOW-5：docstring 主要修正通过，末尾“一律不写”仍过满。**

位置：[live_port_guard.py:1445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1445)。

复现思路：内容部分或全部写入后再发生 I/O 异常，函数失败，但文件可能已经改变；因此“失败方向一律是不写”仍与 `:1431-1433` 自己承认的情况冲突。应区分“返回 False 未调用写盘”和“写盘异常可能已经改变文件”。

其余三项整改**核对通过**：`:1431-1434` 撤销“截断后必坏”，`:1436-1439` 撤销父进程必不误读的推论，`:1439-1440` 明确进程范围。

“发布序先行推进保证……”作为**条件式**成立：实际执行 `:1463` 后，同进程经本函数提交的更小序号不回写。`:1457-1458` 锁超时没有推进，因此不能推广成“每次发布请求都获得该保证”。补充此条件更清楚；锁超时本身不推翻条件式保证。

**其余核对结果与验证限制：**

| 项目 | 结论与依据 |
|---|---|
| round-1 两条顺序假绿 | **核对通过**。装饰器例得到 `1／2／0`；普通跨语句例得到 `2／3／0`，两个门均红。依据测试文件 `:1328`、`:1386`、`:1845`、`:1881`。 |
| `_reachable_prefix` 下标语义 | **核对通过**。`:1217-1221` 只删除后缀，不删除中间元素；保留语句的下标完全不变。顶层 return 后的三个调用已不再计数。 |
| 当前源码 `4／5／6` | **仅存档核对通过，未独立从源码重算**。你限定的 guard 读取段只有 `_publish_ledger`；额外读取 `install()` 的询问尚未得到回复，因此保持原读取范围。 |
| 前三类剪枝及基础回归 | **核对通过**。22 个内存样本覆盖真假分支、四种终结语句、终结语句自身、handler／finally、with 后继、match 及基础局部函数；round-1、自足模式、本轮作用域模式均符合预期。依据 `:1183-1222`、`:1311-1321`、`:1345-1354`。 |
| 源码导出与相等漂移钉 | **核对通过**。方法名导出 `:1061`、白名单调用及精确相等断言 `:1502-1506` 未被本轮削弱；当前源码零命中属于存档结果。 |
| seam 门 | **未见本轮回归，核对通过**。结构门 `:2032-2100`、行为门 `:2102-2163` 未改；结构门所用 `_is_dead_branch` 逻辑也未改。行为结果仅核对存档。 |
| 纯 docstring 性质 | **独立核对通过**。分别对 `46e7bf77`、`45b8e0b4` 与本轮去除 docstring 后比较 `_publish_ledger` AST，均为 **1437 字符、逐字相同**。 |

三份负控存档中的真实节点结果、指定红因、rc 与前后哈希，**人工核对通过**：whitelist 红因在 `:119`，seam 在 `:120`，order 在 `:127/:129`。`r2-precheck-20260914T210549.txt:4` 的 **152 passed／5206 deselected** 及 `:7-13` 的六节点通过也已核对。它们是有效的既有样本，但没有覆盖本次新增反例，不能替代上述缺陷判断。


