**r3 HIGH 在“单实例、固定目标文件”的生产路径下已修复。** 本轮未找到该前提内仍能让旧快照最终覆盖已发布新快照的输入，但回归门尚未完整绑定这一保证。

核对 HEAD 为 `5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a`，全量 diff 恰为三个文件。全程只读、未连接数据库；pytest 结果来自指定存档，补充验证仅使用内存 AST 和调度模型。

以下计数包含本卡问题及仍成立的已登记项；既有多实例一致性缺口另述，不计成本卡 HIGH。

1. **MEDIUM｜本卡：门未覆盖生产派发与取号顺序，AST 也不是自动阻断门。**  
   位置：[test_g3_7_truth_source.py:1277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1277)、`review_service.py:1059-1060`、`evidence-card-states-atomic/ast_gate.py:67-103`。  
   stale 门手工取号后直接调用 helper，绕过了生产调用方。以下都是门未覆盖的路径：

   - 把 `next(_card_states_seq)` 移进 `to_thread` 的 lambda：旧 worker 晚启动便拿到较大序号，重新允许旧快照覆盖新快照。
   - 把 published 记账移到 `os.replace` 之前：高序号发布失败后，仍会误丢低序号待发布快照。
   - 把 `to_thread` 换成同步直调：14 条门没有事件循环响应性断言。

   **复现思路：**分别构造上述负控输入；现有测试没有对应行为断言。前两项“14 条仍可全绿”是静态覆盖判断，未冒充本轮 pytest 实测。AST 脚本只打印结果；同步直调已在内存验证得到 `to_thread=0`，但退出值仍为 `0`。因此只能说人工阅读 AST 输出可识别，不能说 AST 门会阻断。

2. **MEDIUM｜r4 引入：并发门会把合法的过期丢弃判成失败。**  
   位置：[test_g3_7_truth_source.py:1237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1237)、`:1249`。  
   四线程在进入 helper 前取号，却要求 `len(opened) == 4`；正确的过期丢弃可能使实际打开次数小于四。  
   **复现思路：**t0 取得 n 后暂停，让其余线程发布 n+1…n+3，再恢复 t0；t0 正确跳过，门却误红。纯内存调度模型已验证这一矛盾。

3. **MEDIUM｜本卡已登记、仍成立：取消不能释放等待文件锁的 worker，存在共享线程池饥饿。**  
   位置：[review_service.py:722](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:722)、`:1060`。  
   过期判断位于阻塞式锁获取之后，无法提前释放等待锁的线程。  
   **复现思路：**让持锁者停在慢 I/O，逐次确认后续 worker 已开始等待锁再取消其协程，直至共享 executor 的线程全部占用。此处仅确认问题，不讨论配置修法。

4. **MEDIUM｜本卡使既有锁死文字失真，仍未闭合：replace 成功不保证 clear。**  
   位置：[spec.md:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:77)、`review_service.py:732-740,1063,1077-1083`。  
   replace 后目录 fsync、close 或 unlink 失败，都会返回 `False` 并保留／添加脏标记。  
   **复现思路：**采用现有目录 fsync 失败门，即可观察目标已更新但没有 clear。这里只指出失真，不评价锁死文字该不该改。

5. **LOW｜本卡新增 spec：尝试清理被写成了保证无残留。**  
   位置：[spec.md:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:21)、`:151-152`。  
   `MUST attempt` 与实现相符，“所以失败后无 tmp”不成立；新 cleanup 门只覆盖 replace 已成功、tmp 已移走后的清理失败。  
   **复现思路：**先令 write／fsync／replace 失败，再令 unlink 抛 `EACCES`；返回 `False`，但本次 tmp 留存。

6. **LOW｜r4 条件性边界：全局 published 水位没有绑定目标文件。**  
   位置：[review_service.py:678](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:678)、`:723`；测试重定向见 `test_g3_7_truth_source.py:83-84`。  
   **复现思路：**目标 A 的低序号 worker 尚未执行，切换到目标 B 并先发布较大序号，再恢复 A；A 被误丢，尽管 A 从未发布更新快照。  
   需要“旧 worker 存活＋切换目标”这一额外前提；生产目标固定，普通跨测试／跨事件循环单调递增本身不会误丢。

7. **LOW｜存档：静态检查仍未全部保存实际完整 argv。**  
   位置：`_bmad-output/审查/evidence-card-states-atomic/territory-ruff-v2-20260918T194425.txt:21-29`、`ast-v2-20260918T194425.txt:2`。  
   ruff 只有文件列表和结果，没有实际 check／format argv；AST 命令仍含 `<file>` 占位符。  
   **复现思路：**仅凭这些首部不能逐字还原实际静态检查命令。三个 pytest 存档的完整 argv 已补齐，此项不否定它们。

对问题 0–2，顺序和成功语义的具体结论如下：

- **happens-before 成立。** `review_service.py:1033,1052-1060` 中，mutation、序列化、编码、取号均在同一 asyncio 锁内，中间没有 `await`；运行期 published 的比较与更新均在文件锁内，且仅 replace 成功后推进。
- **rollback／pop 不构成本轮绕过。** 序列化失败发生于本次取号之前，回滚恢复进入本次调用前的值；不会回滚掉此前合法调用留下的状态。
- **“更新快照包含全部旧内容”不能按字面理解。** 同一 concept 的旧值可以被后续值正常替代；成立的是同一容器的较新状态覆盖较旧状态。
- **两个实例确实不保证包含关系。** `review_service.py:934,973-985` 为每个实例加载独立容器。先构造 A/B，A 写入 a，B 再写 b，B 的较大 seq 仍能用不含 a 的容器覆盖文件。这是基线已有的多实例缺口；当前生产入口使用 singleton，不能归为 r4 新 HIGH。
- **被取消调用通常不会返回 True。** 正常单事件循环下，旧协程已因取消释放 asyncio 锁并以 `CancelledError` 结束；旧 helper 后来正常返回，不等于原调用方收到成功。
- **计数器持续增长不会自行产生假阴性。** 同一 count 发出的后续序号仍更大；须额外出现第 6 条的跨目标重叠等条件。

七段负控输入核对结果：

| 编号 | 单独拆除的语义层 | 存档失败数 |
|---|---|---:|
| 1 | finally 清理 | 5 |
| 2 | 文件 fsync | 3 |
| 4 | 文件线程锁 | 1 |
| 5 | flush | 1 |
| 6 | 父目录同步改为目标文件同步 | 1 |
| 7 | 过期守卫 | 1 |
| 8 | published 记账 | 1 |

七段均只拆一个语义层；7、8 确实且仅让 stale 门红。1 导致并发门红属于 unlink drain 耦合，不能据此证明实际并发重叠。吞掉 unlink 的 `OSError` 现在会被 cleanup 门拦住；同步直调仍没有自动阻断，见第 1 条。

Requirement 逐段对照：

| spec 行号 | 结论 |
|---|---|
| 8–20 | 正常发布路径的全量快照、编码、flush/fsync、replace、目录同步和一次派发均相符；过期跳过是特殊路径。 |
| 21–26 | 清理尝试、异常归一、不直接写目标相符；无残留绝对承诺不成立。 |
| 28–35 | 线程锁覆盖 helper 全程及跨进程排除相符。 |
| 37–43 | 序号实现相符；同一容器和“仍成功”须受上述实例／取消语义限制。 |
| 45–51 | 正常调用相符；取消后 worker 超出 asyncio 锁生命周期，末句已承认这一例外。 |
| 53–68 | fail-closed、三族异常归一、回滚／保留值相符。 |
| 70–75 | vault 维度脏标记相符。 |
| 77–83 | successful replace 必 clear 仍失真。 |
| 85–88 | 投影与调度真相源分离未被本卡破坏。 |

七个 Scenario 中，新增 stale Scenario 的 helper 行为成立，但生产取号位置尚未被门绑定；失败无残留的描述还受清理本身失败限制。

对照输入的准确分类是 **5 绿＋7 行为红＋2 接口错误**，依据 `redbind-v2-20260918T194249.txt:112-125,175-185`：

| 分类 | 门 |
|---|---|
| 仍绿 | S1、S2、S3 恢复旧值、S4、S5 |
| 行为红 | S3 编码无 tmp；S6 replace 失败清理、fsync 顺序、文件 fsync 失败、目录 fsync 失败、write 失败、cleanup 失败归一 |
| 接口错误 | 并发门：缺 helper 的 `ImportError`；stale 门：缺 counter 的 `AttributeError` |

后两条不是签名 `TypeError`，也不能计作对照输入的行为红；但拆锁、拆守卫、拆记账的负控输入仍分别提供了行为证据。

存档绑定结论是：**已闭合“跑完＋两源码前后与本 HEAD 相同”；尚不能严格证明“运行期间任何时刻源码都未变”。**

| 存档 | 最终结果 |
|---|---|
| `suites-v2…:69-74` | 157 passed，rc=0 |
| `dir-regression-v2…:192-197` | 1927 passed、6 skipped、1 xfailed，rc=0 |
| `unit-v2…:930-935` | 32 failed、5731 passed、44 skipped、13 xfailed，rc=1 |

三份均有完整命令、收工时刻；两源码跑前／收工 hash 与当前文件及指定 HEAD 的 Git blob 完全相同。**前后相等不能排除中途改动再还原**；若要求严格闭合全程不可变，还缺不可变执行快照或运行期间写入隔离证据。没有证据据此反推本轮实际发生过漂移。未采信作废的 `unit-r2`，也未评价 unit 失败的隔离根因。

BLOCKER=0 HIGH=0 MEDIUM=4 LOW=3
