> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R-r3.md)"`
> 审查绑定: `f3546d290da0065c7bad910a939a6ae83a86307f`（该轮送审时的 HEAD；末轮 round-5 的 685e5552 与最终 HEAD 一致，`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a0849e-75a5-78d1-9a3e-30bd6424c91d`

---

**round-3 仍不建议收口：2 HIGH、3 MEDIUM、1 LOW。**

HEAD 与指定的 `f3546d290da0065c7bad910a939a6ae83a86307f` 一致；2581 行证据 diff 与重新计算的 `git diff BASE HEAD` 字节一致。全程未修改文件、未连接数据库，未读取已有 round-3 报告。

**BLOCKER：无。**

**HIGH**

**H1：反向软链仍能绕过 inode 隔离，让登记表显示持锁、实际记录锁已经释放。**

位置：[daily_review_run.py:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:266)，检查在 `:275-282`，触发释放的读取在 `:113`。

预置普通空 `.state.lock`，令 **`.state.json → .state.lock`**。锁路径本身不是软链，`st_nlink == 1`，长度也为零，因此全部检查通过。但 `load_state.read_text()` 跟随 state 的软链，打开并关闭锁 inode，释放本进程在该文件上的记录锁；线程登记表仍报告持锁。

具体失败时序：Web 在外层锁中加载 state，读盘导致失锁，随后隔离软链；runner 因此能取得实际锁。两边各自完成合并、准备发布，Web 保存完成账 A 并返回成功后，runner 发布此前准备的空完成账，A 消失。Web 的 `save_state` 因登记表仍为“已持锁”而跳过重新取锁。

关闭同文件任意 fd 会释放该进程的全部记录锁，这是 Apple 明确规定的语义。[Apple fcntl(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fcntl.2.html)

现有软链门只测 **lock 指向 state**；硬链接门和零字节断言均覆盖不到这个反方向。

**H2：原子发布替换 state 软链后，base 的索引发生变化，runner 第二次保存会整写并丢账。**

位置：[daily_review_run.py:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:315)，查找及整写分支在 `:341-343`，替换在 `:421`。

具体输入与时序：

1. `state.json` 是指向合法 v2 JSON 文件 T 的软链，完成账为空。
2. runner 加载时，将 base 存在 `state.resolve()` 得到的 **T** 下。
3. `ensure_payload:539` 第一次保存，将软链替换为普通 state 文件 **S**。
4. Web 正常取锁，写入完成账 A。
5. Bark 返回后，runner 在 `main:611` 第二次保存；此时按 **S** 查 base，查不到，进入整写分支，将 A 覆盖为空账。

**这个反例中所有写者都可以正确遵守锁。** 两条方向相反的既有门使用普通 state 文件，因此仍绿。独立执行 HEAD 的快照与合并原函数，按上述路径变化建模，得到：

```text
base 索引：T
第二次查询：S
Web 已提交：{"A": "2026-09-09"}
runner 第二次保存：{}
```

**MEDIUM**

**M1：新握手仍不能排除 ready 后暂停，时间门可在生产取锁失效时通过。**

位置：[test_daily_review_run.py:1185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1185)，握手与生产保存之间在 `:1192-1195`，时间判据在 `:1315`、`:1342-1352`。

`blocked` 来自测试自行执行的非阻塞探针。探针关闭后，才调用 `runner.save_state`。

具体反例：撤去生产取锁，子进程在握手后、保存前因调度停顿 2 秒：

- 无锁对照约 2 秒完成，满足 `<5秒`。
- 持锁分支的独立探针确实报告 `blocked`。
- 父进程等待 1.5 秒时，子进程尚未完成。
- 父进程释放后约 0.5 秒完成，时间、退出码和账内容全部通过。

因此握手证明了**探针遇到锁**，没有证明**生产保存被锁阻塞**。探针的 close 不会释放随后尚未取得的锁；问题是两次取锁没有绑定。

**M2：隔离门不依赖 `load_state` 外层锁，R2H1 双变异掩盖了这个缺口。**

位置：[test_daily_review_run.py:1493](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1493)，负控见 [neg-r2 日志:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g67r/neg-r2-20260909T131740.txt:5)。

测试在**第一次读取后**直接换成好文件，第二次读取已经足够救回 A。独立执行 HEAD 原函数及该注入时序：

| 变异 | 活动账保留 | 随后保存保留 A |
|---|---|---|
| HEAD | 是 | 是 |
| **只撤外层锁，保留重读** | **是** | **是** |
| 同时撤锁与重读 | 否 | 否 |

作者负控执行的是最后一行，不能证明外层锁承重。

遗漏的真实失败时序是：只撤外锁后，Web 在**第二次读取坏内容之后、隔离之前**写入好账；runner 随后隔离好账。当前新增门仍会通过。

**M3：刷新新接入 state 后，账内错型日期可以打死刷新。**

位置：[daily_review_pick.py:1249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:1249)，排序键取值在 `:892`，失败在 `:913`。

输入：

```json
{"schema_version":2,"board_last_recommended":{"A":7},"board_done":{}}
```

若 A、B 两块板的 `priority_pick` 相同，排序会比较 A 的 `7` 与 B 的默认 `""`，抛出 `TypeError`；`null`、`[]` 也能触发。当前入口只检查外层是 dict，没有过滤日期值。

这是**既有排序缺陷的新暴露路径**：BASE 的 Web refresh 不传 state；HEAD 传入后，子进程非零退出，由 [review_overview.py:1894](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:1894) 返回 `503 pick_failed`。已用真实排序函数和两块同分节点在内存独立复现；现有错型门仅覆盖外层结构。

**LOW**

**L1：L2 文档整改仍有遗漏，继续把已修复的丢账解释成正确行为。**

位置：[daily_review_run.py:326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:326)；[test_daily_review_run.py:1254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1254)。

合并 docstring 仍称归一化属于主动修改；测试注释更称 v1 补出的空账覆盖 Web 是“正当升版语义”。

具体输入是“v1 缺 `board_done`，加载后 Web 写入 A”。当前实现和专门回归门要求保留 A，上述文字却指导维护者接受覆盖，结论相反。

十个问题的核对结果：

| 问题 | 结论 |
|---|---|
| **1．tmp 四条性质** | `O_EXCL\|O_NOFOLLOW`、异常后尝试 unlink、原子 replace 均保留。unlink 自身失败仍可能留下残渣。正常 tmp 是独立 inode，其 open/close 不释放锁；整体锁独立性仍有 H1。 |
| **2．合并与快照** | 实际快照在**归一化之后**，作者“之前”的自述过期。默认键不算主动修改、版本取 max、缺文件及隔离后记录默认 base 均合理；路径身份变化存在 H2。多请求覆盖同路径 base 的一般反例存在，但当前 Web 同库 load→save 全程串行、runner 独立进程，未发现普通请求触发它。 |
| **3．时间门及对照** | 部分成立，见 M1。对照能排除子进程完全不能运行，不能把等待原因唯一归到生产锁。 |
| **4．refresh 写面** | 通过。state 一次读取、一次解析，不调用保存、隔离或取锁；写面仍为两份投影及目录、原子写临时件。GET 走 `_read_board_done`，不因本轮 `load_state` 加锁而创建锁文件。 |
| **5．撤销三门与幂等** | 三门确实共用同一实现。`already_undone` 能区分“删除过记录／原本无记录”，不能区分拼错、从未完成和重复撤销。这是当前明确接受的接口语义。缺键时不改写正常 state，但仍可能创建锁，损坏 state 仍会隔离。 |
| **6．自动 POST** | 未发现。三处 POST 均在点击处理器内；轮询和 `visibilitychange` 只进入 GET。 |
| **7．升版行为门** | 通过。第一条直接 `save_state(load_state())` 后检查磁盘，测试没有代补键；后二条分别验证字节幂等及隔离原字节，单独不证明升版，组合合理。 |
| **8．写面允许集** | 没有顺手放宽其他路径。仍为完整路径并集上的差集恰等；锁留下内容、直接移入 vault 均会红。`_tree` 和另外三个旧用例与 BASE 源码一致。但结束时零字节不能证明运行期间 inode 独立，见 H1。 |
| **9．重入及清理** | 稳定独立路径下，线程串行、嵌套计数及主体异常清理成立。`fstat` 在 `lockf` 前能拒绝预置硬链接，正常拒绝路径会 close fd、释放 RLock；它不是持续的 inode 独立性保证。若备份工具给活动锁建立硬链接，也会被拒，这是保守拒绝带来的可用性代价。重入门两半有效，但只覆盖外层 with＋直接 save，没有覆盖三层 context 或异常回滚。 |
| **10．自调用** | 稳定路径下至多自调一次；保存主体异常会退出外层上下文。另有条件性清理缺口：若 `LOCK_UN` 或 close 自身抛错，`:311` 的 RLock 释放会被跳过；未确认常规生产触发，未另列缺陷。 |

对负控的最终判断是**不充分**：

- **R2H1** 同时回退两处，单退外锁仍绿，见 M2。
- **R2H2** 对预置硬链接检查承重，但不覆盖 H1。
- **MAX** 新补的 `mine=2 / theirs=1` 确实依赖特判；日志显示两条相关门变红。
- 日志 **`:26-30` 的 M1 是“取锁移出 try 导致 503→500”**，并非 round-2 的时间握手。
- **L3** 实现现在正确，但负控仅回退 `debounced`。单把 `in_progress:1858` 改成 `state_passed:true`，新增门仍绿。
- 两个生产文件当前 SHA256 与负控前后记录一致；这证明还原一致，不能补足上述覆盖缺口。

本轮实际执行了只读的源函数内存验证，以及现有两个前端测试对应的 **6 个 Node 子用例，全部通过**。未运行会落盘的 pytest；文件系统竞态结论依据生产调用链、具体时序及操作系统语义，未将内存验证当作真实多进程验收。


