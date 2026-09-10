> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R-r4.md)"`
> 审查绑定: `c032d74bb4fc1a093bf6201e66f004ece75ac637`（该轮送审时的 HEAD；末轮 round-5 的 685e5552 与最终 HEAD 一致，`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a084b4-fbb8-7cf0-b68b-8180d0204e86`

---

结论：**仍有 1 HIGH、2 MEDIUM、1 LOW，不建议本轮收口。**

已核实 HEAD 为 `c032d74bb4fc1a093bf6201e66f004ece75ac637`，提供的 diff 与实际 BASE→HEAD diff 完全一致。以下并发反例经过独立源码交叉复核；本轮未运行会写临时文件的 pytest，未修改文件、未连接数据库。

**BLOCKER：无。**

**HIGH**

**H1．inode 防护仍不能保证记录锁持续有效，round-3 H1 未闭合。**

位置：[daily_review_run.py:290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:290)、[review_overview.py:2228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2228)。

存在两个具体反例：

- **静态跨库软链，无须运行中改文件。** 预存 `A.state.json → B.state.lock`，B 的 state 是正常独立 JSON，锁文件仍为零字节普通文件。后端线程正常持有 B 锁期间，同进程一次总览 GET 读取 A；`read_text` 关闭指向 B 锁 inode 的描述符，释放整个进程在该 inode 上的记录锁。B 的登记表仍报告持锁。随后 Web 已合并旧磁盘、尚未发布时，runner 可以取得真锁并写入推送账；Web 再发布先前构造的结果，**覆盖 runner 刚写入的字段**。当前检查只比较本库的 state/lock，完全看不到这个跨库别名。
- **检查发生在取锁之前，与作者自述相反。** 实际顺序是 `:275 fstat → :290 stat → :293 比较 → :299 LOCK_EX`。等待期间若一次恢复操作把 state 换成指向本库空锁文件的软链，取得锁后没有复查。Web 随后的读取会关闭锁 inode、释放真锁，再把空文件软链隔离；外层登记仍称持锁。另一进程此时可创建 state、写入完成账 B 并返回 200；原请求从默认账添加 A，再以整个 `board_done` 覆盖 B，**成功点击丢账**。

`os.stat` 跟随软链本身正确，正常独立文件、缺文件分支也没有发现误拒。但当前 R3H1 门只覆盖“调用前已存在的本库反向软链”，上述两条均不在覆盖内。**仅把比较移到取锁后，仍解决不了第一个反例。**

**MEDIUM**

**M1．握手时间门仍能被普通延迟满足，R3M1 负控的失败原因不承重。**

位置：[test_daily_review_run.py:1199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1199)，相关断言 `:1330–1331、:1357、:1366–1367`。

写出 ready 与真正执行生产 `LOCK_EX` 之间仍有窗口。具体反例：**把生产 `LOCK_EX` 替换为两秒延迟，保留登记和测试探测**。无锁组约两秒完成，满足 `<5 秒`；持锁组探测得到 blocked 后延迟两秒，父进程在 1.5 秒时释放，仍满足“释放后完成且不超过五秒”。这道门可以绿，而生产没有取得排他锁。

[R3M1 日志:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g67r/neg-r3-20260909T133832.txt:46)中的变异直接写 `"blocked"`，首先违反无锁对照必须为 `"free"` 的断言。因此目标测试红，不能证明“ready 后停顿”已经被排除。

**M2．新增隔离外锁门仍依赖子进程在 0.6 秒内启动，存在撤锁后误绿。**

位置：[test_daily_review_run.py:1657](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1657)。

`Popen` 后只有 `sleep(0.6)`，没有确认子进程到达取锁点。具体时序：单撤 `load_state` 外层锁、保留重读；子进程启动或调度超过 0.6 秒，父进程先隔离坏文件，子进程随后才取锁、创建带 A 的 state。最终 `:1676` 仍看到 A，**缺少外层锁的实现照样过门**。

R3M2 当次打红有效，但不能证明此门排除了该调度缺口。

**LOW**

**L1．仍有一处把已修复丢账解释成合法升版语义。**

位置：[test_review_overview.py:3489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:3489)。

`_write_v2_state` 仍称空账压过磁盘“是升版语义不是缺陷”。维护者据此排除 v1 并发输入，会把真实丢账误判为允许行为。当前运行代码已经修正，遗留的是误导说明。

十个问题的其余结论如下：

| 问题 | 独立复核结论 |
|---|---|
| **1．tmp 四项保证** | 唯一名、`O_EXCL\|O_NOFOLLOW`、失败清理、`os.replace` 仍在；成功新建的 tmp inode 独立，**tmp 自身的 open/close 不释放锁**。整体持锁保证仍受 H1 影响。 |
| **2．合并与 base** | 实际 base 在**归一化之后**深拷贝，作者“之前”的描述已过时。缺文件和损坏隔离记录默认账，能保护窗口内新建的记录。正常 Web 写请求整段持锁，GET 不调用 `load_state`，未发现普通同库请求互相覆盖 base 的入口；H1 失锁后仍可丢字段。 |
| **3．锁时间门** | 对照组能排除完全无法启动、无法完成等问题，但不能排除 ready 后的延迟，见 M1。探测 fd 在真实取锁前关闭，当前调用中不会释放尚未取得的锁。 |
| **4．refresh 写面** | 成立。pick 对 state 只读；刷新路径不调用会隔离文件的 `load_state`，输出写点仍是两份投影及其目录。 |
| **5．撤销三门及幂等** | 三道门确实复用同一实现。`already_undone` 能区分“删除了一条／原本无键”，**不能区分拼错板名与合法板无记录**；这是明确接受的接口语义。 |
| **6．自动 POST** | 未发现。轮询和 `visibilitychange` 只走 GET，三处 POST 均在点击处理器内。 |
| **7．升版门** | 成立。第一条直接执行 `save_state(load_state())` 后验证版本、原值和精确键集，测试没有自行补键；另外两条分别检查重复发布字节稳定、隔离原字节。 |
| **8．允许集扩三项** | 没有顺手放松其他写面。仍是严格集合相等；空锁、库外路径及 backups 精确文件集合能抓住题述两种改法。`_tree` 和另外三处用例经 BASE→HEAD AST 比对均未变。 |
| **9．重入** | 稳定路径下，线程锁、thread-local 与深度回收配合正确，普通业务异常及多层嵌套未发现泄漏；两半探测分别检查持有和释放。但**登记正确不等于内核锁仍在**，H1 正是反例。 |
| **10．自调用** | 稳定路径下最多额外调用一层；成功登记后 `_state_lock_held` 为真。未发现正常业务异常导致不终止或遗留锁。 |

补充：逻辑 base 键与 resolve 后锁键的分工，在当前固定 `BACKUPS`、按 `vault.resolve().name` 派生路径的生产入口下成立。它仍是按路径保存的快照，并非绑定返回对象的通用事务；顶层键删除也受代码明确声明的有限策略约束。

**负控总判：仍不充分。** R3H1 首次语法无效已正确排除，补跑证明静态本库检查承重；R3H2、R3M3 的变异与目标门相符；L3IP 补跑明确红在新增的 `in_progress` 断言。R3M1 属于错误原因的失败，R3M2 仍有时序缺口，H1 的跨库与等待窗口也没有对应门。


