> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R-r2.md)"`
> 审查绑定: `9e264201d6f97a237a74d7c9a11be406cc0cdac8`（该轮送审时的 HEAD；末轮 round-5 的 685e5552 与最终 HEAD 一致，`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a08488-8356-7e10-a6e3-34e5e4e2a969`

---

**本轮仍不建议收口：2 条 HIGH、1 条 MEDIUM、3 条 LOW。**

HEAD 与指定的 `9e264201d6f97a237a74d7c9a11be406cc0cdac8` 一致；2304 行证据 diff 与重新计算的 `git diff BASE HEAD` 字节一致。全程只读，未修改文件、未连接数据库，也未读取已有 round-2 报告。

**BLOCKER：无。**

**HIGH**

1. **H1：新增锁漏掉了损坏隔离写点，仍能移走 Web 已成功写入的完成账。**

   位置：[daily_review_run.py:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:119)，实际移动在 `:122`；runner 从 `main:508` 在锁外调用 `load_state`。

   具体时序：

   - runner 读到坏 JSON，尚未执行隔离。
   - Web 取得锁，隔离旧坏文件，写入完成账 A，返回 200。
   - runner 按先前的损坏判断执行 `os.replace(state, quarantine)`，**移走此刻已经有效、包含 A 的文件**。
   - runner 返回默认空账，随后保存时磁盘文件缺席，整写空账，A 从活动状态中消失。

   新 fresh-state 门在 **`load_state` 已返回之后**才插入 Web 写入，覆盖不到这个窗口。整改需要让读取、损坏判断和隔离共同受锁保护；只给最后的 `os.replace` 加锁，仍会使用过期判断。

2. **H2：硬链接可以绕过 `O_NOFOLLOW`，重现锁与 state 共用 inode 的失锁。**

   位置：[daily_review_run.py:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:214)，触发释放的读取在 `:95`。

   预先让 `.state.lock` 成为 `.state.json` 的**硬链接**。取锁成功后，`load_state.read_text()` 打开并关闭同一 inode 的另一个 fd，会释放本进程在该文件上的全部记录锁；登记表却仍报告持锁。随后 Web 与 runner 可以同时合并旧状态，再先后发布，覆盖对方字段。

   硬链接共享底层文件，`O_NOFOLLOW` 仅拒绝符号链接；关闭同文件任意 fd 会清除该进程的记录锁。这些行为由 Apple 的 [link(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/link.2.html)、[open(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/open.2.html)、[fcntl(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fcntl.2.html) 明确规定。

   这是沿用原 H3“预置异常锁路径”前提的残留，普通独立锁文件不触发。新增软链门没有覆盖它。

**MEDIUM**

1. **M1：就绪握手排除了导入延迟，但时间门仍可被 ready 后的延迟满足。**

   位置：[test_daily_review_run.py:1181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1181)，判据在 `:1303`、`:1322-1332`。

   具体反例：移除实际 `lockf`，子进程在发出 ready 后、进入保存前停顿 2 秒。此时：

   - 无锁对照仍小于允许的 5 秒；
   - 父进程持锁 1.5 秒时，子进程尚未结束；
   - 父进程释放后约 0.5 秒完成；
   - 退出码、完成时间和最终账内容全部合格。

   因此 ready 表示“导入完成”，还不能证明“已经尝试取得生产锁”。握手应绑定实际取锁入口，例如同一 fd 的真实非阻塞取锁被 `EAGAIN/EACCES` 拒绝后再发出就绪证据。

**LOW**

1. **L1：新增版本号专门门不依赖 `max` 特判。**

   位置：[test_daily_review_run.py:1497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1497)。

   该门设置 `base=mine.version=2`、`theirs.version=99`。即使删除 `daily_review_run.py:298-300`，普通合并也因 mine 未修改版本而选择磁盘的 99，测试仍绿。

   实际遗漏的输入是 `mine=2、theirs=1`：删除特判后会落回 1。**现有 v1 落盘门 `:1533-1537` 会捕获这个回退，所以不是整个测试集失明。**

2. **L2：“非本进程 load 来的 st 就整写”与实际快照判定不符。**

   位置：[daily_review_run.py:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:274)。

   实现只检查**路径**是否有快照，不检查 `st` 来源。具体输入：同一路径此前加载过默认空账，磁盘后来已有 A，再传入一份独立构造的默认空账。实际合并保留 A，并不会按所述契约整写空账。

   当前 Web 串行调用方式避免了正常请求间的覆盖，但不能据此声称快照绑定到了返回对象。另外 `:149`、`:260-265` 仍描述“归一化前快照／缺文件无 base”，与整改后实现相反。

3. **L3：未启动生产器的刷新也可能报告 `state_passed:true`。**

   位置：[review_overview.py:2614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2614)。

   具体时序：上次刷新时 runner 不可达；runner 恢复后，TTL 内再次刷新。`_rebuild_projection:1863-1870` 返回 `rebuilt:false, reason:"debounced"`，没有调用生产器，但响应仍为 `state_passed:true`。

   该字段实际表示路径可用，与旁边“本次有没有把完成账交给生产器”的解释不一致。

十个问题的核对结果：

| 问题 | 结论 |
|---|---|
| **1．tmp 四条性质** | `O_EXCL\|O_NOFOLLOW`、异常后尝试 unlink、`os.replace` 原子发布均保留。unlink 自身失败仍可能留残渣。普通独立锁 inode 下，tmp 的 open/close 不释放锁；整体独立性存在 H2。 |
| **2．合并、归一化与快照** | round-1 H1/H2 的原时序已修复：归一化默认值不再算主动修改，缺文件／隔离后的默认 base 能保留随后创建的账。仍有 H1 的隔离窗口。更大整数版本不会阻止 `setdefault`，未发现“99 导致形态再也推不动”；缺版本、字符串、null、bool 均归一化为 2。路径快照的来源边界见 L2。当前 Web 的同库 load→save 全程串行，GET 不调用 `load_state`，runner 在另一进程，未找到正常 Web 请求覆盖当前 base 的路径。 |
| **3．锁时间门** | 部分通过，M1 仍成立。对照组证明子进程能够完成，不能证明正门的等待来自锁。 |
| **4．refresh 写面** | 通过。picker 从同一次 JSON 解析读取两个键，不调用 runner 的保存或隔离逻辑；写入仍限两份投影及目录／原子写临时件。非 UTF-8 已由 `ValueError` 捕获。 |
| **5．撤销三门与幂等** | 三门现在确实函数复用。`already_undone` 能区分“删掉记录／原本缺键”，不能进一步区分拼错、从未完成和重复撤销；这是明确接受的接口语义。JS 文案已分开。early return 会执行上下文退出并释放两层锁。 |
| **6．自动 POST** | 未发现。三处 POST 都在点击处理器中；轮询和 `visibilitychange` 只进入 GET 路径。 |
| **7．三条升版门** | 第一条直接 `save_state(load_state())` 后检查磁盘，没有测试自行补键，确实验证升版。第二条验证字节幂等，第三条验证隔离原字节；后二者单独不证明升版，组合合理。 |
| **8．允许集扩三项** | 精确新增锁文件这一对象，没有放开任意文件。锁留下非零内容会红；直接移入 vault 会使路径差集及位置断言变红。`_tree` 的 key 并集语义保留，函数及另外三个旧用例与 BASE 源码逐字一致。最终状态断言不能替代 H2 的运行时 inode 检查。 |
| **9．重入与异常清理** | 普通稳定路径下，多线程串行、三层以上重入、相对路径别名及主体异常的计数配对成立。open 拒绝时尚未登记 fd；取锁失败会 close fd 并释放 RLock。重入门“体内拒绝／退出后成功”两半都承重。另有条件性缺口：`:242-244` 的解锁或 close 自身抛错，会跳过 `:245` 的 RLock 释放；本轮未确认常规本地触发，因此未单列缺陷。 |
| **10．自调用终止** | 稳定路径下只自调一次：成功登记后下一次进入保存主体。主体异常会退出外层上下文；未发现自调用本身导致无限递归或漏锁。 |

五条新增门及负控的结论：

| 新门 | 对应修法退回后是否承重 |
|---|---|
| 软链锁拒绝 | 是；不覆盖硬链接 |
| fresh-state 窗口 | 是；不覆盖 `load_state` 内部隔离窗口 |
| upgrade-default 窗口 | 对快照时点承重 |
| schema 单调 | **对新增 `max` 特判不承重** |
| 取锁失败返回 503 | 是；覆盖 done／undone 的 JSON 与表单路径 |

作者后一次负控日志支持“三处 H1/H2/H3 回退分别打红对应门”，还原 hash 也与当前文件一致；它没有回退 `max` 或 M1，不能推出五条门分别承重。较早一次 H1 全绿的实验已在后一次纠正。

本轮实际执行了 HEAD 的 `load_state`／合并函数只读输入验证、内存中的版本特判回退，以及前端原测试脚本的 **6 个 Node 子用例，全部通过**。未运行会落盘的 pytest；两条 HIGH 依据生产调用路径、具体并发时序和文件锁语义判定，未在工作区制造损坏文件或硬链接。
