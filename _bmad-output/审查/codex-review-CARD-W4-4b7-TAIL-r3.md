> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-4b7-TAIL round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4b7-TAIL-r3.md)"`
> 审查绑定: `c118e33e`（审前审后 HEAD 均为此，Codex 正文第 3 段自证）。本轮结论作出后改走「拒绝判定」，新 HEAD `485a1f89` 已另送 round-4
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:4） / `model: gpt-6-astra`（.stderr:7） / `reasoning effort: ultra`（.stderr:11）

---

**本轮 BLOCKER：0；HIGH：0。原 round-2 的三项 MEDIUM 指定复现已修复，但确认了 3 项新增 MEDIUM 假绿，不能判为无回归。**

审查前后 HEAD 均为 `c118e33e37f589292d95a59387a084d6660c4d51`，两份代码文件与该提交一致。跑器及存档为未跟踪文件，按本次读取内容复核。验证采用内存 AST、round-2／round-3 A/B 和文本判据探针；未修改仓库、运行完整负控跑器或连接数据库。

**MEDIUM-1：同名定义全收全展开，会把死代码诱饵变成提前调用，造成双假绿。**

位置：[test_live_port_guard_contract.py:1390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1390)，同文件 `:1323`；不成立的说明在 `:1380-1385`。

复现思路：活的 `h/r` 不做装门操作，在恒假分支放同名 hook／注册定义，再执行 `h(); r(); precheck; hook; register`。

```python
def install():
    def h(): return 7
    def r(): return 9
    if False:
        def h(): _install_audit_hook()
        def r(): register_final_accounting()
    h()
    r()
    assert_neo4j_target_blocked()
    _install_audit_hook()
    register_final_accounting()
```

| 版本 | hook／register／首次 precheck 下标 | 两个顺序门 |
|---|---|---|
| round-2 | 6／7／5 | 均红 |
| round-3 | **3／4／5** | **均假绿** |

把死定义移入一个从未调用的 `unused()`，结果相同。因此，你问的 **①(a)、①(d) 都会发生**：这里按字符串名字匹配，没有真正解析调用绑定。

反方向也实测成立：同名死定义藏提前预检，会使正确顺序得到 `3／4／2`，双假红。**“收多了无害”“方向偏假红”都不能成立。**

**MEDIUM-2：`g = helper; g()` 漏掉提前预检，是新增回归。**

位置：[test_live_port_guard_contract.py:1353](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1353)，同文件 `:1357`；旧说明 `:1251-1253` 仍明确声称覆盖此形态。

复现思路：`helper` 内执行预检，经 `g = helper; g()` 调用，随后依次直接调用 hook、注册和第二次预检。

| 版本 | hook／register／首次 precheck 下标 | 两个顺序门 |
|---|---|---|
| round-2 | 3／4／0 | 均红 |
| round-3 | **3／4／5** | **均假绿** |

回答 **①(c)：现在漏。** 这属于原来明确覆盖的普通别名形态退化，不能仅作为新列举的动态漏面解释掉。

**MEDIUM-3：局部裸装饰器自身的隐式调用被漏掉。**

位置：[test_live_port_guard_contract.py:1343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1343)，同文件 `:1353-1357`。

复现思路：局部 `eager(fn)` 自己执行提前预检，再用 `@eager` 装饰一个普通函数。

```python
def install():
    def eager(fn):
        assert_neo4j_target_blocked()
        return fn
    @eager
    def helper():
        return 7
    _install_audit_hook()
    register_final_accounting()
    assert_neo4j_target_blocked()
```

round-2 得到 `2／3／0`，双红；round-3 得到 **`2／3／4`，双假绿**。

`visit(decorator)` 此时访问的是 `Name("eager")`，不会触发展开。展开被装饰的 `helper` 函数体，补不上装饰器自身执行的预检。

**LOW-1：所谓“自足模式”已不再自行展开局部函数。**

位置：[test_live_port_guard_contract.py:1316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1316)，说明在 `:1301`。

复现思路：同一个 `if True` 内完成 `def helper(): target()` 和 `helper()`，不传函数表调用 `_live_called_names`，实测只返回 `['helper']`，没有 `target`。

两条生产顺序门均传表，因此不另算一个生产门 MEDIUM；但独立探针的识别能力及文档需要据此理解。

**LOW-2：完整仿冒 summary 标题仍能冒充失败原因。**

位置：[negctl_w4_gates.sh:271](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:271)，同文件 `:280-282`。

复现思路：捕获输出中提供完整 `===== short test summary info =====`、精确目标节点和预期关键词，而真正 summary 的该节点失败于另一原因。

提取器会合并两个匹配区段；文本判据探针仍接受。原来的裸 FAILED 行、前缀 nodeid 和交叉配对问题已修复；这里列举的是剩余的文本来源边界。

**LOW-3：缺失取值检查实际失效，但仍拒绝执行。**

位置：[negctl_w4_gates.sh:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:47)，同文件 `:53-55`。

复现思路：参数以裸 `--phase` 或 `--prereq` 结束；调用方仍传入 `"${2-}"`，所以 `need_value` 总能看到第二个实参，随后由 `$2: unbound variable` 退出。

没有假绿，但未走预期的缺值诊断及 `die` 的 rc=2。

**LOW-4：docstring 的“抛异常”仍需限定异常来源。**

位置：[live_port_guard.py:1453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1453)。

复现思路：传入 `{"seq": "x"}`，`:1465` 比较即抛 `TypeError`，尚未推进序号或调用写盘。

因此，“抛异常 ⇒ 写盘调了、序号已推进”**按前文特指 `write_ledger` 的异常成立，泛指本函数所有异常则过宽**。这是文案边界，不是对被守逻辑提出修改要求。

**其余问题的核对结果：**

| 项目 | 结论 |
|---|---|
| round-2 MEDIUM-2 原例 | **核对通过**：新下标 `3／4／2`，两门均红。 |
| round-2 MEDIUM-3 嵌套／传递例 | **核对通过**：分别为 `2／3／1`、`3／4／2`，两门均红。 |
| 两条“不得误红”反向例 | **核对通过**：正确调用顺序、无人调用的普通 helper 均保持绿。 |
| ①(b) 递归／互递归 | **核对通过，限当前静态识别面**：`:1316-1327` 的在途集合截断重复展开，首次展开仍继续扫描其余语句；独立样本均终止且保留提前预检，未发现它单独漏掉应计入的调用名。 |
| `_publish_ledger` 返回 False | **核对通过**：`:1462-1463`、`:1465-1467` 都在唯一写盘调用 `:1469` 前返回；`:1472` 仅释放锁。准确保证是“本调用未调用写盘”。 |
| 条件式推进保证 | **核对通过**：`:1442-1444` 明确锁超时没有推进，实际推进位于 `:1468`。 |

**② `node_result_line` 的恒真问题：核对通过。**

[negctl_w4_gates.sh:210](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w44b7-tail/negctl_w4_gates.sh:210) 当前先 `local … line`，下一行再普通赋值，**没有** `local line="$(...)"` 吞退出码的问题。独立探针中，真命中 rc=0；空、无关节点、前后缀、正文转述和错状态均 rc=1。

正常执行时，`found` 与输出非空同步，双判不是都必需；显式检查 awk 退出码还可拒绝执行错误。这里的 `END { exit(found ? 0 : 1) }` 在 BSD awk、gawk、mawk 没有相关语义差异；本轮仅实际运行本地 awk，另外核对了官方文档。[FreeBSD awk](https://man.freebsd.org/cgi/man.cgi?format=html&query=awk&sektion=1)、[gawk](https://www.gnu.org/software/gawk/manual/html_node/Exit-Statement.html)、[mawk](https://invisible-island.net/mawk/manpage/mawk.html)

**③ summary 格式与空结果方向：核对通过。**

`:271` 的 `=+` 能适应分隔线宽度变化。核对 pytest 9.0.2 官方实现，`-q`、`--no-header` 本身不会改变此 summary 标题形状；极窄宽度也保留等号。[pytest terminal.py](https://raw.githubusercontent.com/pytest-dev/pytest/9.0.2/src/_pytest/terminal.py)、[terminalwriter.py](https://raw.githubusercontent.com/pytest-dev/pytest/9.0.2/src/_pytest/_io/terminalwriter.py)

若禁用 summary、强制 ANSI 颜色等导致提取为空，`:280-285` 的关键词检查失败并置 `ok=1`，结果是**假红，不是假绿**。另外，`-q` 可能影响逐节点结果行或消息截断，不能据此宣称整个跑器兼容任意 quiet 配置。

**⑤ 回归核对：**

| 项目 | 结果与位置 |
|---|---|
| 前三类剪枝本体 | **核对通过**：`:1190-1229`、`:1329-1340` 等，22 个独立样本通过；但与定义表组合后存在 MEDIUM-1 的重新引入死代码问题。 |
| `_reachable_prefix` 下标 | **核对通过**：`:1224-1229` 只截断后缀，保留语句的原下标不变。 |
| 源码导出白名单与相等漂移钉 | **核对通过**：`:1505-1509`、`:1523-1529` 本轮未削弱。 |
| 间接调用识别 | **核对通过**：本轮只改 docstring；`:1116-1127` 已如实登记别名覆盖假红及三类未收集绑定。 |
| seam 两门 | **核对通过，未见本轮回归**：结构门约 `:2035`、行为门 `:2105` 均未改，相关 `_is_dead_branch` 也未改；行为结果仅核对存档。 |
| 纯 docstring 性质 | **独立核对通过**：`_publish_ledger` 去除 docstring 后，与前提及 round-2 的 AST 逐字相同。 |
| 看门／参数／`${text}` | **核对通过**：跑器 `:178-186` 已按进程组杀；指定参数六例均拒绝；`:283/:285` 已使用 `${text}`。未演练实际超时杀组，也不扩成对自行脱组后代的保证。 |

另外保留两项**历史边界**：正确的 hook／注册／预检全放同一个 helper，会因顶层下标相同而假红；生成器 helper 仅创建对象、未迭代，其函数体仍被算作调用，可能假绿。两者 A/B 均在 round-2 已存在。

三份负控存档的节点、红因、rc 和恢复哈希，以及 `152 passed／5206 deselected`、15＋14 探针结果，均完成存档核对。干净源码 `4／5／6` 仍仅为存档结论；本轮遵守读取面，没有额外读取 `install()` 重算。


