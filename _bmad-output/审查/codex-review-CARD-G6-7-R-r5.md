> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R-r5.md)"`
> 审查绑定: `685e5552385f8e8a0d4c782d65ab903e64fa0f7d`（该轮送审时的 HEAD；末轮 round-5 的 685e5552 与最终 HEAD 一致，`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a084c8-191c-7080-9eaa-c6038ebaeef4`

---

**本轮未发现 BLOCKER／HIGH；仍有 2 条 MEDIUM、1 条 LOW。** `flock` 修复成立，但时间门与隔离门尚不能全部判为 PASS。

已核实 HEAD 为 `685e5552385f8e8a0d4c782d65ab903e64fa0f7d`，提供的 diff 与重新计算的 BASE→HEAD diff 字节一致。以下行号均按当前 HEAD。

**BLOCKER：无。**

**HIGH：无。**

在当前本机、固定路径、所有写者遵守协议的生产调用链中，没有找到新的失锁或并发丢账反例。前四轮“额外 open/close 同一 inode 导致失锁”的根因已被替换锁原语解决。

**MEDIUM**

1. **M1：三条时间判据仍可被“等待后无锁继续”的实现满足。**

   位置：[test_daily_review_run.py:1338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1338)、[test_daily_review_run.py:1380](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1380)。

   具体反例：将生产阻塞取锁改成 **尝试 `LOCK_EX|LOCK_NB`，失败则等待 1.6 秒、不重试，随后继续保存**。

   无锁对照立即取得锁；持锁组则等待 1.6 秒，父进程在 ready 后约 1.5 秒释放。子进程随后报告“acquired”，三条时间断言全部满足，实际并未取得锁。两个生产写者因此可能并发合并、发布旧结果。

   我用现有文件的只读描述符验证了这一内核与时间判据组合，结果为：

   ```text
   free-control PASS
   held criteria=[True, True, True]
   actual_lock_owned=False
   acquire_after_release=0.0999s
   ```

   此外，`LOCK_EX→LOCK_SH` 也能满足时间门和现有 `EX|NB` 探测：共享锁会阻挡排他探测，却允许两个生产写者并存。

   **这是测试覆盖问题，当前生产 `LOCK_EX` 没有上述错误。** 应补充两个生产写者不能同时进入临界区的验证。

   作者的 `sleep(2)` 负控确实会红，但首先红在 **无锁对照的 `acquired-entered < 0.5`**，尚未执行持锁组第三条断言；[负控日志:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g67r/neg-r4-20260909T140215.txt:11)不能证明所声称的第三条承重。

2. **M2：隔离门的握手仍未建立所需顺序，撤掉外层锁仍存在误绿时序。**

   位置：[test_daily_review_run.py:1567](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1567)、[test_daily_review_run.py:1743](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1743)。

   具体时序：

   - 撤掉 `load_state` 外层锁。
   - 子进程写出 ready，尚未取得真锁时被抢占。
   - 父进程看到 ready，先隔离坏文件。
   - 子进程恢复执行，取得锁、新建 state 并写入 A。
   - 最终 `board_done == {"A板": TODAY}`，测试仍绿。

   握手排除了慢启动，却没有保证缺锁实现中的子写者先于父隔离完成写入。**当前生产外层锁正确；未闭合的是测试判别力。**

   `M2WAIT` 同时撤外层锁、撤新握手，测试的已经不是当前门；当次失败不能证明上述窗口被消除。

**LOW**

1. **L1：inode 拒绝报文仍陈述已经不成立的失锁机制。**

   位置：[daily_review_run.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:307)。

   输入为 `state.json → state.lock` 时，检查正确拒绝，但报文仍称“读 state 的一次 close 会把锁一起释放”。换成 `flock` 后，这个原因已经不成立，容易误导排障。

   应说明锁与数据不得共用文件身份。round-4 原 L1 的升版误导注释则已修正。

十个问题的独立结论如下：

| 问题 | 结论 |
|---|---|
| **1．tmp 四项保证** | 保留唯一名、`O_EXCL\|O_NOFOLLOW`、异常清理及同目录原子 `os.replace`；独立 tmp 的 open/close 不释放 `flock`。清理是**尝试 unlink**，unlink 自身失败或进程被强杀仍可能留残渣；原子发布也不等于断电持久性保证。 |
| **2．合并与 base** | 实际在**归一化之后深拷贝**，默认空账不算主动修改；版本单调取大。缺文件、隔离重建记录默认 base，可以保留窗口内新建的账。当前 Web 同库 load→save 全程持锁，GET 不更新 base，runner 独立进程，未找到普通请求覆盖快照的路径。它仍是按路径保存的有限协议，并非绑定返回对象的通用事务。 |
| **3．时间门及对照** | 对照确实承重，能拦住无法完成及无条件长延迟；但不能证明持锁组真正拥有排他锁，见 M1。 |
| **4．refresh 写面** | 成立。pick 从同一次解析读取两个账本，不调用 runner 的隔离／保存；持久输出仍为两份投影，另有目录与临时件操作。 |
| **5．撤销三门与幂等** | 三个 helper 均唯一定义并复用。`already_undone` 能区分“删了一条／原本缺键”，不能区分拼错、从未完成与重复撤销，符合已声明语义。缺键不改写正常 state；首次取锁及损坏隔离仍可能动盘。 |
| **6．自动 POST** | 未发现。三处 POST 均在点击处理器内；定时轮询和 `visibilitychange` 只进入 GET。 |
| **7．升版行为门** | 有效。首门直接执行 `save_state(load_state())` 后检查版本、原值和精确键集，没有自行补键；另两门分别检查重复发布字节稳定和隔离原字节，单独不证明升版。 |
| **8．写面允许集** | 有意新增空锁文件这一项，但未放开任意写入。严格差集相等、锁大小为 0、库外路径及 backups 精确文件集合，能抓住题述两种改法。`_tree` 与另外三个既有调用函数经 BASE→HEAD AST 比对均未变化。 |
| **9．重入登记** | 稳定路径下正确：同线程复用 fd，其他线程串行，多层嵌套及普通业务异常正常回收。受控三层嵌套／异常／线程验证通过，最终登记为空。探测两半分别证明与排他探测冲突及退出后释放，但不能单独证明生产锁是排他的，见 M1。 |
| **10．save 自调用** | 稳定路径下最多额外一层；成功登记后持锁判断为真。未发现普通异常导致无限递归或遗留锁。 |

还应明确三项运行前提，适合登记移交，**不据此新增本卡 HIGH**：

- **活动锁文件及父目录的身份必须稳定。** 有 `backups` 目录写权限的恢复／清理工具若删除并重建锁文件，旧持有者仍锁旧 inode，新写者可锁新 inode。当前代码没有这条替换路径。
- **持锁期间不得任意 fork／共享 fd。** `fork`／`dup` 共享同一打开文件描述；子进程显式解锁可影响父进程，保留继承 fd 也可能延长锁寿命。当前持锁段未发现该调用链。普通异常退出关闭最后引用后会释放内核锁，零字节锁文件本身不会造成陈旧死锁；`push.sh` 的目录锁则是独立机制。[Apple flock(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html)
- **需要提供原生 flock 语义的平台。** 除网络文件系统差异外，Python 明确说明某些系统会用 `fcntl` 模拟 `flock`，不能把本机结论直接推广到所有 Unix。[Python fcntl 文档](https://docs.python.org/3/library/fcntl.html#fcntl.flock)

本轮未修改文件、未连接数据库，也未运行会落盘的 pytest。实际完成了只读内核锁实验、四组合并原函数输入验证，以及现有前端行为门的 **6 个 Node 子用例，全部通过**；这些不替代完整 HTTP／落盘回归。


