> 批次: BATCH-2026-09-05-第十二批 · 车道 Y7 · 卡 CARD-W4-4-settle-atomic round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-4-settle-atomic.md)"`
> 审查绑定: `工作区（03ac8bf8 + 本卡 diff，round-1 之后按其 HIGH-1/HIGH-3/MEDIUM-5/6 + LOW-9/10 整改过 ⇒ 失绑，见验收单 §九)`
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle` / `model: gpt-6-astra`

---

**结论：内存结算的原子性修复成立，但整道门仍不能判为通过。** 未发现 BLOCKER；确认三条 HIGH，其中“stderr 异常跳过退出”是既有缺口。

复核对象为 `03ac8bf8de4acd164d51c92db001ae42ada14a73` 上的当前工作区 diff。全程未修改文件；补充验证仅使用内存 AST、内存 pytest 插件和合成 `sys.audit` 事件，没有建立真实连接或写入账本。

**HIGH 1 — seam 可以在记账之前抛出异常，且身份复核并非必然执行。**

位置：[live_port_guard.py:645](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:645)、同文件 :840；[conftest.py:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/conftest.py:143)；[guard_plugin.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/guard_plugin.py:54)。

seam 先执行，`:648` 才记账。因此替换函数抛出 `RuntimeError` 后，连接虽然被阻断，账本却仍为零。身份检查只发生在显式调用 `assert_guard_live()` 时：独立安装后、最后一个用例边界之后，以及仅加载插件的 session 检查之后，都没有必然到来的复核；临时替换后在边界前恢复，同样不会被身份比较发现。

**独立实测：**安装成功→替换 seam 为抛异常函数→发送受拦审计事件→捕获异常，得到 `blocked=0, unaccounted=0`，子进程退出 **0**。

处置方向：seam 的异常不能绕过记账与失败结算，不能仅依赖“下一个用例边界”发现漂移。

**HIGH 2 — 目标预检失败会留下已经生效、却没有最终结算器的审计门。**

位置：[live_port_guard.py:764](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:764)，以及 :685–699、:767–777。

顺序确实变成了“装 hook→目标预检→注册结算”。首次预检抛出时，结算注册和身份复核都不会执行，而不可撤销的 audit hook 已经生效。

**独立实测：**设置 `W4_GUARD_REQUIRE_BLOCKED_TARGET=1`，不设置 `NEO4J_URI`；捕获安装异常后继续发送受拦审计事件，得到：

```text
audit_installed=True
final_registered=False
installed=False
unaccounted=1
进程退出码=0
```

正常 pytest 若让安装异常向外传播，会失败；上述假绿要求调用方捕获异常后继续。但“预检失败就是拒绝装门”的描述已经不符合实际状态。顺序提前没有新增门前窗口，新增的是**部分安装后没有结算**的失败模式。

处置方向：让不可撤销的 hook 生效与退出结算保障绑定，覆盖预检失败路径。

**HIGH 3 — stderr 写入异常仍能跳过迟到路径的 `_exit(3)`。**

位置：[live_port_guard.py:654](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:654)、同文件 :664、:1262–1275。

迟到分支已经记账，但 `_exit(3)` 前的 `print(..., file=sys.stderr)` 在异常保护之外。stderr 已关闭时，`ValueError` 会越过强制退出；下面只保护 `flush()` 的 `try` 无济于事。普通最终结算的打印也有同类结构。

**独立实测：**提前注册一个排在最终结算之后执行的 atexit 回调；空账结算完成后，该回调使用已关闭的内存 stderr，发送审计事件并捕获异常。得到 `finalizing=True, blocked=1, unaccounted=1`，进程仍退出 **0**。本例未替换 seam。

这是**既有问题，非本次新增**，但直接否定“判迟到就必然就地退出 3”的承诺。

处置方向：让日志和落盘异常不能跳过强制退出，例如将退出放入可靠的 `finally` 路径。

**MEDIUM 4 — 同一内存快照没有保证文件发布顺序，迟到账本仍可被旧零账覆盖。**

位置：[live_port_guard.py:1248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:1248)、同文件 :1252、:1206、:1226、:653–664。

以下交错在代码中可达：

1. 最终结算取得零账快照，释放状态锁，尚未写盘。
2. 迟到线程记账并重写文件为 `unaccounted=1`。
3. 迟到线程执行 `_exit` 前，结算线程用旧快照重新 `open(path, "w")`，写回零账。
4. 迟到线程退出 3。

结果仍是 **rc=3、文件零账**。两条写盘路径没有共同的发布顺序控制；这是静态控制流证明，**本轮未做落盘实测**。

此外，`:1227–1228` 吞掉写盘异常，可能留下旧文件、空文件或不完整 JSON。该策略可以保住非零退出，却不能保证文件一致。即使 I/O 全部成功，`:1261` 的额外条件 `blocked>0 and effective_status==0` 也允许 **`unaccounted=0` 时退出 3**。

处置方向：统一最终写盘与迟到重写的发布顺序，并把账本可靠性、真实退出判据与“双向等价”承诺分清。

**MEDIUM 5 — `precheck_done` 表示“曾经成功”，后续预检失败不会撤销豁免。**

位置：[live_port_guard.py:1071](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:1071)、同文件 :1093–1104、:435–443。

成功路径单向置 True，失败路径仅抛异常。因此“先成功→配置改变→再次检查失败→捕获异常继续”的序列中，`begin_item(..., True)` 仍发豁免票。这与 `:1101`“预检失败时豁免必须保持关闭”的无条件描述不符。

内存实测确认：首次未设置 URI 时检查成功，随后检查失败，闩仍为 True，受拦审计事件被记为 `advisory=1, blocked=0`。该次后续失败原因为诊断解释器缺少 neo4j，验证的是**失败不撤闩**，不涉及 URI 解析正确性。

这**不是正常首次 pytest 配置路径放宽**；首次 configure 失败会终止会话。

处置方向：将闩绑定到已验证配置并处理失效，或者明确限定配置不可变，收窄注释与测试承诺。

**MEDIUM 6 — 变异裁判把“没有运行到指定断言”也算作 KILLED。**

位置：[mutation_teardown.py:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-4/mutation_teardown.py:102)、同文件 :115–130、:325–334。

`run_tests()` 只检查子进程是否返回 0，不确认指定 nodeid 的断言实际执行；`run_probe()` 收不到 `PROBE-JSON` 就返回 False；汇总把所有 False 都标为 `FAIL(KILLED)`。所以 import、configure、collection 错误也能“杀掉变异”。

这与脚本 `:9–10` 明确声称的“被 import 错误或更早防线喂饱算 SURVIVED”相反。最终存档的源码摘要前缀与当前文件吻合，但没有保存契约失败明细，不能据此独立证明每项失败身份正确。

处置方向：将启动错误、未执行和预期断言失败分别判定，只有最后一种计为指定防线杀死变异。

**MEDIUM 7 — 多条 AST 契约比它们声称锁住的性质宽。**

位置：[test_live_port_guard_contract.py:645](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/unit/test_live_port_guard_contract.py:645)，以及 :658–678、:742–775、:833–869。

直接抽取现有测试函数、在内存提供候选 AST 后，以下错误结构仍被判通过：

- “同一把锁”用例接受 `with self.unrelated_lock`，并接受先 `return self._ledger_locked()`、再写不可达的 `self.finalizing=True`。
- “无条件调用”用例接受 `if False: _finalize_race_seam_hook()`。
- 同一用例接受 `consumer(_finalize_race_seam_hook())`，尽管返回值被使用。
- “先安装后预检”用例接受死分支里的 `_install_audit_hook()`。

此外，禁止锁外读的用例只查旧拼写 `_FINALIZING`，没有禁止 `STATE.finalizing`；禁止嵌套锁的用例只是四个方法名的黑名单。

这些反例证明**测试不能支持其完整宣称**，不代表当前实现本身使用了这些错误结构。

处置方向：精确检查接收者、赋值、调用形态与可达顺序，并以行为验证补足关键同步性质。

**MEDIUM 8 — 直接调用链没有嵌套取锁，但 `record()` 的诊断格式化保留了重入入口。**

位置：[live_port_guard.py:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:302)、同文件 :310、:378。

`record()` 持有不可重入锁时调用 `repr(address)`。若地址对象的 `__repr__()` 回调 `STATE.ledger()`，后者再次获取同一锁，形成自死锁；若格式化抛异常，则发生在计数增加之前。

这是**既有记账诊断结构**；本次迟到分支也开始经过它。此判断不涉及重新评审地址分类函数。

处置方向：不要在状态锁内执行可重载的地址格式化，并保证诊断失败不影响记账。

**LOW 9 — before 证据把未经确认的线程完成状态打印成“已经落账”。**

位置：[before-repro.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-4/before-repro.py:124)、同文件 :163–168。

`join(10)` 后没有检查线程是否结束或记账完成，就打印“已……落账”。尤其 before-1 的 rc=0、文件零账，也与超时后线程尚未完成相容。

这不是证明历史复现没有发生，而是该存档不能独立证明那个阶段已经完成。

处置方向：用完成事件或明确账面断言确认落账，超时标为复现无效。

**LOW 10 — 部分时机注释仍与实际接线冲突。**

位置：[live_port_guard.py:934](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/live_port_guard.py:934)、同文件 :119–120、:1166；[guard_plugin.py:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/tests/support/guard_plugin.py:34)。

`:934` 声称两个 canonical 调用方都在 configure 期或更晚，实际插件在 import 期 `install()`，启用 REQUIRE 时当场执行目标预检。`:1166` 仍写“所有 cleanup / atexit 之后”，与紧接着的 LIFO 说明冲突。`:119–120` 的最终结算后无法改退出码说法，也需要与当前迟到机制及真正剩余的解释器清理边界区分。

处置方向：按实际调用时点统一注释。

其余要求的明确判定如下：

| 核对项 | 结论与依据 |
|---|---|
| 默认 seam 是否惰性 | **成立。** `live_port_guard.py:568–586` 只有 docstring；`:645` 丢弃返回值，没有等待或环境读取。`:840` 确实有身份比较，但不是使用返回值决定放行。“无条件”应限定为进入非自证受拦分支之后。 |
| 内存结算是否同锁、是否还有原来的第三落点 | **成立。** `:302–327` 与 `:339–341` 使用同一实例锁；置位与快照之间不解锁。除构造期 `:274` 初始化外，运行期标志读写均在锁内。对正常完成的 `record()`，旧的“既没进快照又没判 late”交错已消除；不能据此推出强制退出必然完成。 |
| 最终结算是否只取一次快照 | **成立。** `:1248` 取 dict，`:1252` 显式传递，`:1255–1261` 读取同一 dict。当前调用链不会进入 `:1204` 的 `ledger=None` 分支。迟到快照属于另一条有意追加的路径。 |
| 是否存在直接锁嵌套 | **未发现。** `_ledger_locked()`、`_unaccounted_locked()` 不再取锁；`begin_item()`、`_mark_precheck_done()` 没有调用其他取锁方法。`:648` 的 `record()` 返回时已释放锁，`:653` 才进入迟到重写。外部格式化回调的例外见 MEDIUM 8。 |
| 正常 integration/e2e 豁免是否改宽 | **没有。** `:1283–1304` 的规则未改；成功及未配置 URI 的预检路径都会置闩。独立路径若只调用 `install()+begin_item()` 而不做预检，会一直不豁免，这是已声明的收紧。 |
| configure 失败与原 fixture 失败是否等价 | **不等价。** 内存 pytest 实测，同一个 `RuntimeError` 在 configure 抛出是 `INTERNALERROR / rc=3`，在 session autouse fixture 抛出是 `setup ERROR / rc=1`。上移可以合理地提前失败，但不能称失败形态相同，也不能把所有 rc=3 都解释成未结账。 |
| 新竞态探针是否把“没有发生”算通过 | **该探针没有这种简单漏洞。** `lifespan_isolation_guard_probes.py:1236–1245` 未到 seam 会打印 FAIL，未发生迟到退出则 rc=0；`:78–90` 还核对退出码。但它在完整结算返回后才释放线程，覆盖不到写盘竞争。 |

作者自述需要修正或限定的清单：

- **(a)** 同锁原子化属实；“只有两种归宿”适用于正常完成的记账操作，不能扩展成“迟到一定退出 3”。
- **(b)** 当前最终结算传递同一个 dict 属实；“在 (a) 后完全没有独立可观测差异”过宽。上述文件竞争中，传旧快照会写零账，M2 再取快照则可能写到迟到账，文件内容可不同。
- **“变异实测中探针杀不掉 M2”——未判定。** [mutation_teardown.py:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-4/mutation_teardown.py:182) 明确 `probes=[]`；两份存档的 M2 都只列契约结果，缺少实际探针 SURVIVED 输出。
- **(c)** 迟到记录增加 `total/blocked/pending`、不看豁免属实；“重写保证 rc 与文件双向等价”不成立。
- **(d)** 顺序描述属实，但“预检失败仍等于拒绝装门、无需结算”的解释不成立。
- **(e)** 上移和闩实现属实；正常首次路径未放宽，但失败形态改变，后续失败也不撤销已置位的闩。
- **(f)** 默认 no-op、返回值丢弃、存在身份复核属实；“被替换后三种行为都不放松整道门”过宽，异常可以跳过记账，复核也不是必然执行。
- **“探针复现的是注入制造的确定性交错，而非自然时序”——属实。** `:1219–1223` 设置等待，`:1239` 完整结算，`:1242` 才释放线程。


