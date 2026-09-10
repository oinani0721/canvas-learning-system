> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R.md)"`
> 审查绑定: `57c932e30ccc698ae125595fa5432bc9ab8c5cf8`（该轮送审时的 HEAD；末轮 round-5 的 685e5552 与最终 HEAD 一致，`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a08471-5cbb-7812-80d9-8abb27374862`

---

**不建议收口：发现 3 条 HIGH、3 条 MEDIUM。** 当前 HEAD 与指定对象一致，1993 行证据 diff 与重新计算的 `git diff BASE HEAD` 字节一致。

全程只读、未连接数据库。执行了不落盘的合并函数复现、真实 CLI 异常复现和内核锁语义探测；未运行会创建文件的 pytest。

**BLOCKER：无。**

**HIGH**

1. **H1：升版补出的空完成账会覆盖已经成功落盘的用户记录。**  
   位置：[daily_review_run.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:100)、[daily_review_run.py:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:270)。

   失败时序：runner 读取缺少 `board_done` 的 v1，记录原始 base，再自动补 `{}`；扫描期间 Web 成功写入 `{"A": today}`；runner 随后保存，因为“空字典与 base 缺键不同”，覆盖成 `{}`。**加性升版因此删除了一次已确认的完成操作。**

   只读执行实际 `load_state`／合并函数得到：v1 场景丢 A，完整 v2 场景保留 A。现有 runner 向门明确排除了缺键 v1，双向门可以同时绿。保存后也未更新原 `st` 或 base，因此推送后的第二次保存仍存在这个窗口。

2. **H2：缺文件或损坏隔离后的 `base=None` 分支，不保留随后新建的有效账。**  
   位置：[daily_review_run.py:259](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:259)，来源分支为 `:87`、`:119`。

   失败时序：runner 首次读取时没有 state，或刚隔离坏文件，得到默认空账和 `base=None`；扫描期间 Web 创建有效 state 并记录 A；runner 保存直接 `return mine`，**甚至不读取现在已经有效的磁盘账**，再次清掉 A。

   文件锁只让两次发布串行，不能修正这个覆盖选择。只读合并复现确认丢账。这属于本卡承诺解决的并发残留仍未收口。

3. **H3：新锁文件跟随软链，既能失去互斥，也能突破库外写面。**  
   位置：[daily_review_run.py:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:199)。

   `os.open(lock, O_RDWR | O_CREAT)` 没有拒绝软链，也未保证锁与 state 使用不同 inode。

   - 预置 `state.lock → state.json`：取得记录锁后，`load_state:90` 的读盘关闭同 inode 的另一个 fd，释放整个进程在该文件上的记录锁，但 thread-local 仍报告持锁。Web 合并完成、尚未 replace 时，runner 可以写入新推送账；随后 Web 发布旧合并结果，抹掉新账。
   - 预置锁软链指向 vault 内**尚不存在**的节点文件：取锁的 `O_CREAT` 会在那里创建零字节文件，违反库内零写入。

   本机内核只读探测确认：原锁 fd 保持打开时，额外同 inode 的 open/close 足以释放记录锁。现有锁门只构造普通独立锁文件，捕获不到此问题。

**MEDIUM**

1. **M1：新增取锁异常绕过既有 503 转译，退化为裸 500。**  
   位置：[review_overview.py:2262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2262)、同文件 `:2344`。

   `state_locked` 在捕获 `save_state` 的 `try/except OSError` 外面。若 `backups` 被普通文件占位，或锁文件没有写权限，异常会在取锁的 mkdir/open 阶段逸出。BASE 中目录创建失败会返回 `503 state_write_refused`；HEAD 返回 500，零 JS 表单也失去动作专属错误页。

2. **M2：新接入的 state 读取会让非 UTF-8 损坏文件拖垮手动刷新。**  
   位置：[daily_review_pick.py:1238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:1238)，新增入口为 `review_overview.py:2545`。

   输入包含非法 UTF-8 字节，例如 `0xff`：`read_text` 抛 `UnicodeDecodeError`，不属于这里捕获的 `JSONDecodeError/OSError`。生产器退出，refresh 返回 `503 pick_failed`；此前刷新不传 state，不受该文件影响。

   使用真实 CLI、stdin 输入该字节且不传 `--write`，已复现退出码 1。新增损坏门只覆盖可解码的 UTF-8 文本。

3. **M3：锁时间门可以把子进程启动延迟误判为锁阻塞。**  
   位置：[test_daily_review_run.py:1300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1300)。

   失败情形：移除实际锁；对照子进程正常完成，正门子进程因调度或导入延迟，直到父进程释放后的第 1.6 秒才执行保存。此时仍满足：持锁 1.5 秒时未退出、`finished >= released`、释放后五秒内完成、账内容正确。

   子进程记录了 `started`，父进程却未使用，也没有抵达取锁点的握手。对照组能排除“完全跑不起来”，**不能证明正门等待由锁造成**。

**LOW：无。**

对十个问题的完整核对如下：

| 问题 | 结论 |
|---|---|
| **1．tmp 四条性质** | 原 tmp 的 `O_EXCL\|O_NOFOLLOW`、异常清理和 `os.replace` 原子发布均保留。清理是尝试 unlink，unlink 自身失败仍可能留残渣。普通独立锁 inode 下，tmp 的 open/close 不释放锁；整体锁安全存在 H3。 |
| **2．合并与快照** | 原始内容深拷贝能准确记录读取快照，但把归一化空账视作覆盖权限不合理，见 H1；缺文件／隔离分支见 H2。模块快照表确实每路径只有一份，但当前 Web 的 load→save 全程串行，GET 不调用 `load_state`，runner 又在另一进程；未找到正常生产路径下另一个 Web 请求覆盖当前 base 的时序。 |
| **3．时间门** | 有 M3 假阳性。完全不执行的子进程不能满足超时、退出码和输出要求，但释放前尚未到达取锁点的子进程可以。 |
| **4．refresh 写面** | `--state` 只参与一次 JSON 读取，不调用 runner 的保存或隔离路径；发布目标仍是两份投影及目录创建。①②的 state 零写入承诺成立。 |
| **5．撤销三门与幂等** | 同源与容纳门是真正函数复用；长度门只共享 `_BOARD_NAME_MAX`，判断和错误构造在 `:2635/:2710` 各写一份，不能称作“三个共享函数”。`already_undone` 只区分“删除过键／原本缺键”，不能区分拼错与重复撤销；JS 成功文案也未区分。另“不落盘”须限定有效 state：损坏 state 仍会被 `load_state` 改名隔离，首次取锁也可能创建锁文件。 |
| **6．自动 POST** | 未发现。三处 POST 都在点击处理器内；timer 和 `visibilitychange` 只进入执行 GET 的 `poll`。 |
| **7．升版行为门** | 没有测试自己补键。首门直接 `save_state(load_state())` 后检查磁盘版本、键集和原值，真实升版删除后会红；第二、第三门分别验证字节幂等、隔离原字节，单独不证明升版。 |
| **8．扩集是否改松** | 没有泛化放宽：仍比较前后路径并集，完成写面仍精确等于三项。锁中留下内容、直接把锁路径移进 vault 都会红。`_tree` 和另外三个既有用例与 BASE **源码逐字一致**。但这些是普通夹具的最终状态断言；位置检查使用字面路径，不能替代 H3 所缺的运行时软链防护。 |
| **9．重入登记表** | 稳定路径、独立锁 inode 下，多线程串行、三级以上嵌套和常规主体异常的计数配对成立；相对路径及稳定软链别名经 resolve 归一。重入门的“体内拒绝／退出后成功”两半都承重，但没有覆盖 H3，也未覆盖全部异常组合。 |
| **10．自调用终止与释放** | 未发现自调用本身造成无限递归或常规异常漏锁：成功登记后下一次调用进入主体，主体异常会退出外层上下文。M1 是异常响应转译缺口，与递归终止问题不同。 |


