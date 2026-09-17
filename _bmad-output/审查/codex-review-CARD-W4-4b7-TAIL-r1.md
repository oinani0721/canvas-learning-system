> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-4b7-TAIL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4b7-TAIL.md)"`
> 审查绑定: `45b8e0b4`（代码 commit；审时 HEAD 即此。本轮结论作出后按其 MEDIUM-1/2 整改，新 HEAD `a307de45` 已另送 round-2）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `reasoning effort: ultra`（.stderr:9）

---

**本次限定面内未发现 BLOCKER / HIGH；发现 3 项 MEDIUM，不能认定四笔债已全部收口。** 两个 AST 门存在可复现的假绿，另有跑器隔离方式与自述不符。

已核 HEAD 为 `45b8e0b4`，两份代码文件与该 SHA 一致。仅执行了抽取 helper 的内存 AST 探针；未修改仓库、运行 pytest／负控跑器或连接端口。下述测试通过记录均注明为存档核对。

**MEDIUM-1：别名覆盖会把实际的非白名单调用认成白名单调用。**

位置：[test_live_port_guard_contract.py:1129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1129)、同文件 `:1147`。

复现：

```python
with self._lock:
    f = self.ledger
    f()
    f = self._ledger_locked
```

独立探针返回 `['_ledger_locked']`，漏掉实际调用的 `ledger`。后一次赋值即使放在 `if False:` 内，也得到相同结果。原因是别名表只保留最后收集到的绑定，然后用它解释所有调用。

这是**已声称覆盖的普通 Assign 面内漏洞**；`:1099-1100` 所称“过近似只会假红”不成立。保留每个别名曾绑定的方法集合，就能避免这一覆盖问题，无须实现完整数据流分析。

**MEDIUM-2：第四类剪枝会剪掉真实执行的预检，两个顺序门可以同时假绿。**

位置：[test_live_port_guard_contract.py:1253](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1253)、`:1283`；调用方 `:1746`、`:1781`。

复现思路：令 `@eager` 装饰器立即调用下面的 `helper`，再按以下顺序放置语句：

```python
@eager
def helper():
    assert_neo4j_target_blocked()

_install_audit_hook()
register_final_accounting()
assert_neo4j_target_blocked()
```

真实的第一次预检发生在装门前；新版却将装饰函数体剪掉。独立探针得到 hook／register／precheck 下标 `1 / 2 / 3`，两个门均通过。旧版遍历函数体，会发现提前预检。

装饰器会在定义期间获得函数对象并执行，并不要求源码再次出现函数名。因此“未被 Name 提及 ⇒ 函数体不可达”不成立；漏掉真实调用也**不只导致假红**，后面的同名调用可以掩盖它。[Python 函数定义语义](https://docs.python.org/3/reference/compound_stmts.html#function-definitions)

**MEDIUM-3：负控修改的是工作树，临时目录保存的是备份。**

位置：[negctl_w4_gates.sh:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:96)、`:148`、`:177`。

`DST` 指向 `$TREE/$GUARD_REL`；变异和 before 阶段均直接覆盖工作树文件。因此“对照输入只写进临时副本”的自述不成立。

复现思路：在变异写入后、pytest 结束前读取工作树，会看到自死锁代码；此时另一个测试进程也可能执行它。正常退出后的哈希一致只能证明恢复成功，不能证明运行期间隔离。挂起时 EXIT trap 尚未执行，SIGKILL 也不会执行该 trap。

**LOW：①白名单剩余漏面。**

位置：[test_live_port_guard_contract.py:1061](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1061)、`:1077`、`:1107-1147`、`:1422-1425`。以下均可直接作为 AST 复现输入：

| 形态 | 结论 |
|---|---|
| `getattr(self, name)()` | 漏，属性名必须是字面串。 |
| `self.__getattribute__("ledger")()` | **会红**：内层 `self.__getattribute__(...)` 本身是直接调用，不在白名单。 |
| `object.__getattribute__(self, "ledger")()` | 漏，接收者不是字面 `self`。 |
| `[self.ledger][0]()`、容器存取、`invoke(self.ledger)`、`partial(self.ledger)()` | 漏，不传播容器、参数或包装器中的 callable。 |
| `f=self.ledger; g=f; g()`、元组解包、临界区外绑定后在区内调用 | 漏，未跟踪这些绑定关系。 |
| 临界区内局部函数包含 `self.ledger()` | 直接 AST 扫描能够发现；未调用的函数体也可能导致假红。 |
| 临界区外定义 helper，再于区内调用；或 helper 经参数调用绑定方法 | 可以漏。 |

**方法名集外的 callable 也会漏。** 例如会取得该实例 `_lock` 的外部闭包挂到 `self.callback`，再写 `f=self.callback; f()`，不会进入新增识别面。继承方法、类体赋值产生的 callable／描述符也不一定进入该集合。字面 `self.callback()` 仍会被直接门拒绝。允许读取面不足以断言当前已有这些对象。

普通 Assign、AnnAssign、两种海象、字面 getattr 的基础案例，以及源码导出白名单和相等漂移钉，**核对通过**，位置为 `:1061`、`:1116-1147`、`:1404-1406`。

**LOW：③第四类剪枝还有反射、跨语句与文案边界。**

位置：[test_live_port_guard_contract.py:1222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1222)、`:1253-1289`。

- `locals()["helper"]()` 无须出现 `Name("helper")`，可以误剪。`globals()` 的类似反例需要函数确实绑定到全局；普通局部 helper 不能直接由 `globals()` 取得。
- 装饰器注册后经 registry 调用，同样可能没有函数名引用。
- `return helper` **包含 Name**：同一分析子树内能够继续展开闭包；跨 install 顶层语句则丢失关联。
- 普通“先定义、后调用”翻红可以作为明确的重构限制接受，但不能据此声称整体只会假红。另有合法反例 `def helper(old=helper): target()`：默认参数引用既有同名绑定，会使根函数体展开，推翻“根 FunctionDef 必不展开”的文案。
- 原有漏面仍在：`:1746`、`:1781` 逐语句扫描，没有先截断 `install().body`。复现为顶层 `return` 后依次放 hook／register／precheck，仍能得到顺序绿。

前三类局部剪枝则**核对通过**：`:1151-1171` 的字面真假判断成立，`_is_dead_branch` 逻辑未改；`:1175-1190`、`:1268-1277` 按字段截断也成立。`Try` 的 handler／finally 独立保留；finally 改变控制转移不会返回原 body 的后继语句；`with.__exit__` 抑制异常后从 with 之后继续；match 各 case body 独立处理。终结语句自身的调用仍被保留。

**LOW：④跑器绑定了 nodeid 子串，但未严格绑定结果行与失败原因。**

位置：[negctl_w4_gates.sh:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:162)、`:191-203`。

- `"$node PASSED"` 带空格，所以 `<node>_extra PASSED` 或 `<node>[参数] PASSED` **不能冒充**，这一点核对通过。
- 缺少左边界，`other/<完整nodeid> PASSED` 或正文转述 `expected <nodeid> PASSED` 可以命中；纯文本探针已复现。
- after 将 `FAILED` 身份和关键词分别在整份输出搜索，没有绑定到同一节点的实际失败断言，也未验收其 rc。复现思路：目标节点红在另一断言，预期关键词由其他失败、捕获输出或回溯源码提供，仍可过判。

**本次三份存档的实际红因核对通过**：whitelist `:73-76` 是 `ledger` 白名单断言；seam `:73-77` 是次数为 0；order `:75-84` 是指定顺序断言。脚本的不足不等于这些已读结果无效。

另有一个参数纪律例外：同脚本 `:41-43` 遇 `--help` 立即退出，因此 `--help --nonsense-arg` 不会拒绝后面的未知参数。普通未知参数路径 `:34/:44/:55` 及其存档六例，**核对通过**。

**LOW：⑤docstring 仍把失败结果与保证范围说得过满。**

位置：[live_port_guard.py:1430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1430)、`:1434-1436`、`:1447-1458`。

- “截断之后失败 ⇒ `json.loads` 必报错”不成立。可能 JSON 已完整可读，而 close／延迟 I/O 才报告错误；这是“缺失／无效／旧内容”之外的可能结果。真正缺少结尾的字典 JSON 半截通常无效，不能泛称任意半截都会恰好合法。[close 的延迟错误语义](https://man7.org/linux/man-pages/man2/close.2.html)
- “推进发布序 ⇒ 父进程不会把陈旧零账误认为空账”推不出来。复现思路：原文件就是合法零账，较新非零账在截断前写失败，旧零账仍在；阻止后续旧快照回写并不会更新这份文件。父进程是否另用退出码、序号判定，属于未读取面。
- `_PUBLISHED_SEQ` 只约束共享该进程状态、经过本函数的发布。另一个进程不受此序号约束，因此“此后一律被拒”需要明确进程范围。
- 若允许符号链接／FIFO进入写入路径，还需分别考虑链接目标和流式消费、阻塞语义。**`write_ledger` 实现未在授权行段内，不能声称已独立核清这些路径。**

以上仅登记文档准确性与移交边界，不将既有发布设计算成本卡逻辑缺陷。**纯 docstring 修改核对通过**：独立重算两版去除 docstring 后的 AST，均为 **1437 字符、逐字节相同**。

**② seam 行为门核对通过，但它明确锁定“一次事件、一次 seam、一次受拦记账”的契约。**

位置：[test_live_port_guard_contract.py:2031](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:2031)，以及 `:2040-2063`。

拆成两层函数，只要仍调用被包装的 seam 一次，行为门不会因此误红；把 seam 移出 `_audit_hook` 后，原有结构门可能先红，位置 `:1966-1969`。若合法需求改成一次事件执行多次 seam 或增加受拦计数，则需要同步修改契约，当前精确计数确实会红。

这里依赖正常的 CPython audit 分发及 hook 安装状态，**不是本机 3.14.x 独有语义**：钩子按注册顺序调用，首个异常中止后续分发；没有同一次显式 `sys.audit` 自动重复分发给同一注册项的通常语义。其他钩子抢先抛错、重入等环境变化仍可能影响测试。[Python audit 文档](https://docs.python.org/3/library/sys.html#sys.audit)

5432 是否实际运行服务无关，因为没有连接。它若被加入 `BLOCKED_PORTS`，`:2032` 会明确报红，避免对照静默失效。

**⑥单节点负控已跑完可以确认；作者给出的完整控制流解释尚不能盖章。**

跑器 `:61-62`、`:157`、`:187` 确实只选择白名单结构节点；whitelist 存档 `:10/:67/:133` 各收集 1 项，正常退出且 attempts=0，`:182-186` 记录前后哈希一致，**核对通过**。

但 `_audit_hook`、`audit_hook_alive()` 及相关 fixture／plugin 不在授权读取面，无法独立确认“必在 record 前抛 `_SelfTestBlocked`”的具体分支顺序。

若改成目录级，只要某个测试或 fixture 到达变异后的 `record()`，就可能在第二次取得非重入锁时挂住；跑器没有超时，EXIT 恢复也要等进程结束。指定一个 AST nodeid 能缩小执行面，不能单独证明 pytest 收集、fixture 和插件全过程都不会调用 `record()`。

最后，`guard-selftest-20260914T204935.txt:6/:9-14/:17` 中的 **152 passed、5206 deselected、三个反向锚及新增行为门逐节点通过，存档核对通过**；这些既有样本未覆盖上述两处新复现的假绿。
