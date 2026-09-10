> 批次: BATCH-2026-09-07-第十三批 · 车道 U7 · 卡 CARD-RV-W4-4 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-W4-4.md)"`
> 审查绑定: `da690bf8`（零代码卡：本卡 commit 只含 `_bmad-output/`，五个代码文件 blob sha 与 `da690bf8` 逐字节相同 ⇒ `git diff --stat da690bf8 HEAD -- . ':(exclude)_bmad-output'` 恒空；Codex 正文亦自证「本轮 HEAD 前后均为 da690bf8817adc4a84b20d59a1b8d8db4a578969」）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard` / `model: gpt-6-astra`

---

**结论：部分认可。** HIGH-1 的指定三步主症已闭合；HIGH-3 的迟到异常路径也已闭合，但普通最终结算仍有同型残留。报告关于「生产路径语义面为空」的断言不成立。

本轮 HEAD 前后均为 `da690bf8817adc4a84b20d59a1b8d8db4a578969`。全程未修改文件、未连接端口。补充实验只执行内存中的源码片段，没有运行会写文件的原复现脚本或完整探针。

**HIGH 1 — 普通最终结算仍能因错误报告失败而跳过强制退出**

位置：[live_port_guard.py:1281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:1281)；定性表 `:115-118`、`:161`。

依据：`write_ledger()` 抛出异常后，代码执行：

```python
except Exception as exc:
    print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
```

这条打印位于后面的 `:1291-1303` 保护块之外。若 stderr 再抛异常，执行到不了 `:1288` 的退出判定，更到不了 `:1304` 的 `_exit()`。因此，「两处打印/落盘全在 try 内」不成立。

独立片段实验提供 `blocked=1, unaccounted=1, reported_status=0`，令路径转换抛 `OSError`、stderr 为已关闭的 `StringIO`，以 atexit 回调执行这段原代码，得到 **rc=0**。没有实际写盘。**完整 guard 与真实文件系统故障组合未验证**，但越过退出判定的控制流已确认。

建议：HIGH-3 改判为「迟到路径原症闭合，普通最终结算仍有同型残留」。定性表 `:161` 的无条件「`unaccounted>0 ⇒ rc=3` 成立」也需收窄；这处残留已足以否定该全称承诺。

**MEDIUM 2 — `except` 按动态调用范围捕获异常，不按“注入点自己抛出”鉴别来源**

位置：[live_port_guard.py:654](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:654)；契约 `:855-858`；定性表 `:102-107`。

依据：`try` 内只有 `_finalize_race_seam_hook()`，只能说明后面的直接 `STATE.record()` 调用不在保护区内，不能证明捕获的异常一定来自替换函数中的那条 `raise`。

作者三跑未覆盖的输入包括：

- **默认函数调用期间的 SIGINT 或跟踪回调异常。** 我保留 docstring-only 默认函数及其身份，通过 trace 在进入该函数时发送 SIGINT。原 `try` 吞掉 `KeyboardInterrupt` 并继续；裸调用对照则向外传播。trace 回调自身抛 `RuntimeError`，结果相同。
- **调用建立时的运行时异常**，例如递归深度或资源不足导致的异常。函数体 AST 为空不能排除这些异常；本轮未实测其具体触发条件。
- **替换函数调用下层代码所传播出的异常。** `except` 同样会接住它们，并不会回滚下层调用已经产生的副作用。

而且三跑只覆盖了随后得到 `RECORD_BLOCK` 的形态。若得到 `RECORD_ADVISORY`，HEAD `:661-682` 会正常返回：原本中断调用的异常可能变成继续执行；若得到 `RECORD_LATE`，则进入强制退出路径。这些结果不能由三种异常类型的非豁免测试代替。

建议：保留「异常不再直接跳过后续记账」的局部结论，撤回「严格只是注入点自己抛出的异常」「生产路径新增语义面为空」。以上不等于发现了新的非豁免端口放行漏洞。

**MEDIUM 3 — 行号重合不能作为缺陷未修的硬证据**

位置：[triage-20260908.md:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-rv-w44/triage-20260908.md:40)，另见 `:19`、`:39`。

依据：报告将「引用行与 HEAD 行号完全重合」称为“未修”的硬证据。行号只能定位；即使某几行逐字相同，上下游控制流、调用关系或锁的实现也可能改变缺陷是否成立。

此外，指定的 `93d47028..360a4cb2` diff 是历史对象，不能自动代替 HEAD 未获准读取的片段。

建议：以 HEAD 中缺陷成立所需的完整关系作为依据。此次没有足够原文的项目保留「未验证」，具体见末表。

**LOW 4 — 探针覆盖面的描述误把异常消息当成了实际输入**

位置：定性表 `:129-132`；指定 diff 中 `360a4cb2` 版 `lifespan_isolation_guard_probes.py:1384-1391`。

依据：报告说只测了 stderr 已关闭，并将“替换成 `write()` 抛异常对象”列为未覆盖。但所给历史源码实际是：

```python
class Boom:
    def write(self, *a, **k):
        raise ValueError("I/O operation on closed file")
```

随后执行 `sys.stderr = Boom()`。这恰好就是替换写入抛异常对象；错误消息包含 closed file，并不代表真的关闭了 stderr。

建议：按实际构造描述覆盖面。**HEAD 探针是否仍保留该实现未验证**，因为其 HEAD 正文不在限定读取面中。

对你五个问题，另有以下明确核验结果：

1. **HIGH-1：同意指定三步主症闭合，局部对照同构。**  
   HEAD `:654-660` 捕获 seam 异常后继续记账；最新复现输出确实记录了 HEAD 的 `3/1/1` 与裸调用对照的 `0/0/0`。`high1-repro.py:67-73、157` 的变换就是恢复记账之前的裸调用，与旧复核 `:18-20` 描述的失效机制一致。**没有找到使这三步不同构的行。** 但这只能称为该缺陷的局部还原，不能证明整个旧工作区逐字重建。父提交缺少该注入点，不能承担同一 seam 复现的对照角色，这个更正合理。

2. **`BaseException`：存在作者未覆盖的语义面。**  
   见 MEDIUM 2；默认函数体为空不足以排除调用期间的异常。

3. **HIGH-3 迟到分支：所列抛异常形态均能到达 `_exit()`。**  
   HEAD `:678` 是 `except BaseException`。独立 CPython 3.14.4 片段实验中，关闭的 `StringIO`、`write()` 分别抛 `ValueError/RuntimeError/KeyboardInterrupt/SystemExit`、stderr 为 `None`、fd2 映射至只读 fd，**七例均 rc=3**。  
   但“必然”需要限定：`write()/flush()` 若阻塞、不返回，`except` 无法使执行继续。等待不返回的写入实验超时。这不否定旧异常路径已经修好。

4. **撤回「⇔」文字不会弱化现有两个场景的断言。**  
   指定历史 diff 中，迟到场景仍要求正账与 rc=3 同时成立；无连接场景仍要求零账与 rc=0 同时成立。它们能发现各自场景的退化，仍然承重，但不能证明全称双向等价。`:1288` 确实允许第二个析取项在 `unaccounted==0` 时触发退出；该状态的完整可达性本轮未另行复现。**HEAD 探针判据是否与历史实现相同未验证。**

5. **十条状态逐项核验如下。**「未验证」表示限定读取面不足，不表示作者判错。

| 条目 | 本轮独立结论 |
|---|---|
| HIGH-1 | **同意主症闭合**；`:587-590` 确认身份复核非必然的限制已如实声明。不同意语义面为空。 |
| HIGH-2 | **HEAD 未验证**。历史 diff 支持预检早于注册，且契约确实钉住该顺序；当前对应函数和契约行不在允许片段中。 |
| HIGH-3 | **迟到原症闭合，整体需改为部分闭合**，见 HIGH 1。 |
| M4 | **同意未修**。HEAD `:1233` 的覆盖写入、`:1253/:1279` 两条独立调用及 `:1288` 第二析取项均已核到；未运行竞态。 |
| M5 | **HEAD 未验证**。历史 diff 支持措辞更正和单向置位；当前 `:1116-1131` 不在允许片段中。 |
| M6 | **未验证**。缺允许读取的 `mutation_teardown.py` 原文。 |
| M7 | **至少一项确认未修**：HEAD `:860-869` 的判据仍接受 `if False: _finalize_race_seam_hook()`；其余四项的 HEAD 同一性未验证。 |
| M8 | **未验证**。缺 HEAD 锁定义、`record()` 与 `ledger()` 的对应原文；不能用表内摘录代替独立核验。 |
| LOW-9 | **未验证**。缺允许读取的 `before-repro.py` 原文。 |
| LOW-10 | **部分核到**：HEAD `:1193` 已更正；另一处更正见历史 diff。HEAD `:119-120` 未获读取。若其原文如表所引，确与迟到分支的退出能力存在张力；报告所称残余窗口必然存在及其边界，本轮均未验证。 |


