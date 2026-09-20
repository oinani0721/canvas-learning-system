线程锁确实修复了同一进程内的临时文件交错写入，但仍有 **1 项 HIGH：取消后的旧快照可以晚于新快照发布**。

已核当前三文件与 `b173eb44` 一致。全程只读，未运行 pytest；下述新增负控输入的通过情况属于静态推导，并发实验只验证无文件调度前提。

1. **HIGH — 已取消请求的旧快照可以覆盖后来成功的新快照。**  
   位置：[review_service.py:1036](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:1036)，以及 `:704、:710`。  
   A 已捕获旧 `payload`，其线程开始后、取得文件锁前暂停；取消 A 协程后，B 可以取得协程锁，发布新快照、清空 dirty 并返回 `True`；随后 A 恢复，取得线程锁并发布旧快照。整个过程完全串行，仍会发生数据回退。  
   **复现思路：**在 A 到达 `:704` 前设置调度屏障，取消 A，等 B 保存完成后再释放 A。

   无文件并发原语实验得到 `B-new → A-old`；两次派发的对照输入只有 `B-new`，因为取消后的 A 不再派发第二次 replace。这是本卡把完整发布放进一次 `to_thread` 后引入的路径。

2. **MEDIUM — 慢 I/O 加连续取消可以耗尽共享线程池。**  
   位置：`review_service.py:704、:1036`。  
   持锁线程卡在慢 I/O 时，已启动但被取消了协程的后续 worker 仍会阻塞于 `Lock.acquire()`；积累到线程池容量后，无关 `to_thread` 也无法开始。  
   **复现思路：**用三个 worker，让第一条持锁等待，依次启动并取消三个保存协程，再投递一个无关 `to_thread`。

   无文件实验确认这一条件性饥饿。事件循环仍可响应；释放持锁线程后恢复。正常未取消路径只有一个保存 worker，且 helper 不反向获取协程锁，**未发现内生死锁**。

3. **MEDIUM — 12 条门仍有契约覆盖缺口。**  
   位置：[test_g3_7_truth_source.py:1170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1170)、`:1212–1217、:1243`。  
   并发门在 replace 返回时停止观察，未覆盖目录 fsync、close、finally unlink；最终 `keys() <= {...}` 也允许空文档或多个线程键的混合文档，不能证明“某一次完整快照”。  
   **复现思路：**将清理移出线程锁，安排前一线程清理与后一线程创建 tmp 交错；当前临界区断言不会直接观察该重叠。

   另有两个经静态检查仍可让 **12 条全绿**的负控输入：

   - 给 `review_service.py:717` 的 unlink 增加 `except OSError: pass`：没有门注入清理失败。
   - 把 `:1036` 改为同步直接调用 helper：没有门检查事件循环响应或线程派发；第十二条本来就直接调用 helper。存档里的 AST 检查能识别此变化，但它不属于这 12 条门。

4. **MEDIUM — “successful replace 必须 clear”仍与实现不符。**  
   位置：[spec.md:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:69)，对应 `review_service.py:711–717、:1039、:1053`。  
   replace 成功后，目录 open/fsync/close 或清理失败，都会使方法返回 `False`，跳过 clear。  
   **复现思路：**只让父目录 fsync 抛 `OSError`；现有目录门已经直接观测到新快照存在而 dirty 未清。这里只判文字失真，不评价锁死文字该不该改。

5. **LOW — 部分存档仍缺完整命令或最终版本绑定。**  
   位置：[suites-final-20260918T182259.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-card-states-atomic/suites-final-20260918T182259.txt:2)、`territory-ruff-r3-20260918T182114.txt:1`、`pyright-r3-20260918T181720.txt:1`。  
   suites 命令仍含 `<9 个点名文件>`；territory/ruff 绑定 `7c504f13`；pyright 只有结果和 rc，没有命令、HEAD、hash。  
   **复现思路：**逐项比对首部即可看到这些缺项；它们不等于最终源码检查失败。

**关于线程锁及调用路径（问题 0–1）**

`review_service.py:704–717` 确实覆盖 open、write、flush、文件 fsync、replace、目录 fsync、close 和 unlink。函数是模块级并不能绕锁，直接调用也必须取得同一把锁。

在给定生产入口与 helper 内，未发现两条线程同时操作该 tmp 的路径。这个结论限于指定读取面，不等于已经检索全仓所有独立写入者。上述 HIGH 是**发布顺序错误**，不是临界区重叠。

**五段负控输入（问题 2）**

| 负控输入 | 拆除的功能层 | 存档结果 |
|---|---|---|
| r3-1 | unlink 清理 | 3 failed / 9 passed |
| r3-2 | 文件 fsync | 3 failed / 9 passed |
| r3-4 | `threading.Lock → nullcontext` | 1 failed / 11 passed |
| r3-5 | flush | 1 failed / 11 passed |
| r3-6 | 父目录对象改成目标文件 | 1 failed / 11 passed |

五段均只拆一层，均选择 12 条、排除 21 条，`rc=1`。

五组 before/after hash 全部一致，但恢复到的是 `48116cade…cc55c`，即搬锁前版本；最终源码是 `64d62ddd…182e59`。我另核了搬锁前后两个生产函数 **AST 相同**，测试与 spec **字节相同**：可采信为相同行为的负控证据，不能称为最终 HEAD 的逐字节负控证据。

**Requirement 逐段对照（问题 3）**

| spec 行号 | 核对结果 |
|---|---|
| 8–12 | 全量快照、嵌套结构及序列化参数符合；取消后的过期发布见 HIGH。 |
| 14–18 | 预编码、tmp、flush、文件 fsync、replace、目录 fsync、一次派发均符合。 |
| 19–24 | 保证清理尝试；不能保证清理 I/O 自身失败时无残留，后文已明确这个例外。 |
| 25–26 | 给定正常文件路径下，不直接写目标；replace 前失败保留旧目标。 |
| 28–35 | 线程互斥及仅覆盖进程内的边界符合；没有保证快照发布顺序。 |
| 37–43 | 未取消时符合；取消后 worker 不再位于协程锁持有期间，末句已经说明例外。 |
| 45–50 | fail-closed 在 mkdir 前返回，符合。 |
| 52–60 | 三类异常的归一、回滚/保留内存及异常范围，符合。 |
| 62–67 | dirty 使用 vault/concept 对，符合所给实现及门。 |
| 69–75 | replace 即 clear 的触发条件失真，见 MEDIUM；清标记不恢复丢失值的解释成立。 |
| 77–80 | 投影与调度真相源的区分符合方法说明；读取面未包含调用方，不能据此确认所有调用方均遵守。 |

**旧实现对照输入（问题 4）**

整体换回 `9c4e7e82` 后，静态分类为 **5 绿、6 条行为红、1 条导入错误**：

| 门及当前行号 | 对照输入结果 | 性质 |
|---|---|---|
| S1 原子发布 `:765` | 绿 | 既有行为回归 |
| S2 scope fail-closed `:794` | 绿 | 既有行为回归 |
| S3 编码失败不开 tmp `:824` | 红 | 本卡行为 |
| S3 恢复旧值 `:856` | 绿 | 既有行为回归 |
| S4 清全部 dirty `:875` | 绿 | 既有行为回归 |
| S5 vault dirty 隔离 `:897` | 绿 | 既有行为回归 |
| S6 replace 失败清理 `:932` | 红 | 本卡行为 |
| S6 fsync 顺序及长度 `:964` | 红 | 本卡行为 |
| S6 文件 fsync 失败清理 `:1013` | 红 | 本卡行为 |
| S6 目录 fsync 失败 `:1046` | 红 | 本卡行为 |
| S6 write 失败清理 `:1118` | 红 | 本卡行为 |
| S6 四线程串行 `:1159` | `ImportError` | 旧版无 helper，不能算并发判据将其打红 |

**薄代理与目录门（问题 5–6）**

`_WriteRefusingFile` 属于真实文件 I/O 边界上的失败注入，没有替换 service 内部方法。当前路径执行真实 open、真实 enter、write 抛错、真实 exit/关闭，未见额外语义偏差。`__getattr__` 不能代理所有特殊方法，但现生产路径不依赖这些方法。

目录门已消除按调用次数判断的问题：额外文件 fsync 不再因此误红，目录改成文件已被 r3-6 拦下。对象类型、父目录 inode、文件先于目录以及最终目标新内容，共同约束了当前路径。

但它证明的是**向父目录 fd 发起 fsync，并报告注入的失败**；目录分支在调用真实 fsync 前就抛错，不能单独证明目录成功同步。`st_ino` 也不是跨设备唯一身份。这些不推翻当前门的有效性，但限制了其证明范围。

**最终存档绑定（问题 7）**

三份首部 HEAD 均为 `b173eb4480d8ca00b98474d576c3c4c723fe32b3`；两源码完整 SHA-256 均与当前文件及该提交逐字一致。unit 末尾两项 hash 也与首部一致。

| 存档 | 开跑时间，+0800 | collected | passed | skipped | xfailed | failed | pytest_rc |
|---|---|---:|---:|---:|---:|---:|---:|
| suites-final | 18:22:59 | 155 | 155 | 0 | 0 | 0 | 0 |
| dir-regression-final | 18:24:23 | 1932 | 1925 | 6 | 1 | 0 | 0 |
| unit-final | 18:34:49 | 5820 | 5731 | 44 | 13 | 32 | 1 |

末尾定位分别是 `suites-final…:67–68`、`dir-regression-final…:190–191`、`unit-final…:928–932`，分类数字全部闭合。

因此可以接受：**日志绑定最终两源码，三次运行均已完成；unit 未全绿。** 尚缺 suites 完整 argv、suites/regression 各自结束 hash；现有绑定也不能证明整棵运行依赖不变，或绝对排除中途修改后复原。未采信作废的 unit-r2，也未评价 unit 失败成因。

BLOCKER=0 HIGH=1 MEDIUM=3 LOW=1
