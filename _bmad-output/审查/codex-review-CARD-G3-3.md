已核对 HEAD=`47a37a0c141530de806ec1b0367c48c23d96e6cc`，八个实质文件均与该 commit 一致，`docs/` diff 为空；未修改仓库。

本轮实跑：旧门 **125 passed**、新门 **21 passed**；隔离镜像中原始负控 **7/7 KILLED**；原并发脚本 **3 轮均 rc=[0,0]、账本 2 行、attempt=2、lost_update=False**。[负控结果](/private/var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/g33-review-original7-5o8eh11x/mutation-results.json) · [并发结果](/private/tmp/g33-independent-concurrency-47a37a0c-0839.json)。这些通过结果没有覆盖下面的反例。

## BLOCKER

无。

## HIGH

**H1．后端线程交接仍会释放另一个调用正在持有的 POSIX 锁。**

位置：[learning_event_log.py:158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py:158)、同文件 `:252`。

`_write_lock` 先退出，随后才 `os.close(fd)`。我用原模块、真实线程和外部进程，仅通过 trace 控制交接时序：

- A 停在关闭 fd 前；B 已取得记录锁并完成 `_read_all`。
- 外部抢锁：A 关闭前为 `BLOCKED`，关闭后为 `ACQUIRED`。
- 外部调用与 B 均返回 `True`，最终 IDs=`['first','shared','shared']`。

因此，同一调用内使用同一个 fd **仍不足够**；前一个调用的关闭会释放后一个调用的锁。建议让线程锁覆盖 **open→lock→scan/write→close** 的完整生命周期。

**H2．新增 `splitlines()` 会拆开合法 JSON，造成幂等回退。**

位置：[learning_event_log.py:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py:183)、[start-exam-board/SKILL.md:469](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/start-exam-board/SKILL.md:469)。

后端写入 `ensure_ascii=False` 的合法文本后，扫描却把 U+2028、U+2029、U+0085 当成记录分隔符。我逐个对照两个 commit：

- 同一事件调用两次：基线返回 `[True, False]`，本次返回 `[True, True]`。
- 物理 JSONL 从基线 **1 行**变为本次 **2 行同 ID**。
- 建板名称含 U+2028：基线两次执行累计 **240 字节、1 行**；本次 **480 字节、2 行**。

这是新增分行方式的问题，不是已豁免的旧子串查重问题。建议只按物理 LF 分隔，并增加合法 Unicode 文本的幂等回归门。

**H3．账本最新时刻不等于已应用水位 W，自动标记会阻断恢复。**

位置：[learning_event_log.py:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py:204)、同文件 `:232`；契约依据：[schema:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/docs/learning-events-schema-v1.md:266)。

端到端实测：

| 步骤 | 观测 |
|---|---|
| E1@10:00 正常评分 | rc=0，W=10:00 |
| E2@10:01 遇到 CAS 冲突 | rc=1，账本已有 E2，W 仍为 10:00 |
| 补录 E3@10:00:30 | append=True，自动标 `out_of_order=True` |
| 下一次评分 | rc=1，报“晚于水位线……被伪装成乱序的真实后继” |

该账本的独立校验器仍返回 **0**，在线恢复则被 [quiz-answer/SKILL.md:1748](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1748) 拒绝。

两种分叉方向都存在：**账本最大值 L>W** 时，`W<事件≤L` 被错标；**L<W** 时，`L<事件≤W` 会漏标。后者可来自节点状态导入、账本缺失或历史行被排除。

建议依据受同节点锁保护的实际 W，或可证明的已应用边界分类。`<=` 本身与在线 A3 严格 `>W` 自洽，错的是基准。`_instant(naive)` 实测返回 `None`：不猜时区合理，但忽略该历史并继续分类，不能保证标记正确。

**H4．改成单次 `os.write` 后，短写被报告为成功。**

位置：[learning_event_log.py:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py:250)、[start-exam-board/SKILL.md:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/start-exam-board/SKILL.md:474)。

使用真实内核文件大小限额，逐字运行基线与目标源码：

| 写点 | 实际落盘 | 基线 | 本次 |
|---|---:|---|---|
| backend，5000 字符 payload | 1000 字节，无 LF | 返回 False，记录错误 | **返回 True，无错误** |
| start-exam-board | 80 字节，无 LF | 打印写入失败 | **打印事件已落日志** |

残行风险基线已有；**把残行报告成成功**是本次回退。建议在同一持锁 fd 上写完整或检查返回字节数，并进入既有失败分支。

**H5．新增跨写点互斥没有覆盖 quiz-answer 的查重。**

位置：[quiz-answer/SKILL.md:2844](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2844)、同文件 `:2886`。

“二次查重”仍查询旧 `_rows` 快照，取得账本锁后没有重新查重。我在主块准备取得账本锁时，让真实 backend `append_event` 先写入同一事件：

`backend=True；quiz rc=0；账本 IDs=['quiz:audit#q1','quiz:audit#q1']；validator rc=1`。

这是**本卡新增并发覆盖面的缺口**。建议持锁后通过同一 fd 重读、检查 ID 及信封一致性，再决定追加。

**H6．新增 CAS 是检查后替换，仍不能保证保住同时发生的正文编辑。**

位置：[quiz-answer/SKILL.md:2923](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2923)、同文件 `:2669`、`:2737`、`:152`。

实际是 **3 个 `_cas_guard` 调用＋1 个 A3 `cas_conflict` 调用**。四处检查后都还有临时文件写入；主块还要 flush/fsync，之后才 replace。块自身没有在这段间隙另写 NODE，但不参与锁协议的外部写者可以写。

实测主块 CAS 返回后追加正文：**rc=0，attempt=1，外部正文消失**。A3 在临时文件刚创建后发生外部编辑，同样 **rc=0、callout 保留、外部编辑消失**。

这是新增防线未完成其声称场景，**不是把基线原本无 CAS 的问题重新算成回归**。将检查移到临时文件准备完毕后只能缩小窗口；完整保证需要编辑与发布串行化，或保留冲突版本，普通重读＋`os.replace` 不构成原子 CAS。

## MEDIUM

**M1．主块 CAS 冲突路径不满足“节点＋账本零写”。**

位置：[quiz-answer/SKILL.md:2900](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2900)、同文件 `:2923`；[test_g3_3_cas.py:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_3_cas.py:385)。

实测在检查前编辑正文：**rc=1、正文保留、attempt 未推进，但账本已新增 1 行**。CAS 测试只检查节点未推进，没有在冲突时断言账本未变。

若保留 write-ahead，应明确为“拒绝发布，事件已入账待恢复”，并测试该状态；不能继续称为 `_write_face` 定义下的零写。

**M2．七条负控没有覆盖所有新增防线；A3 两道门存在确定性漏检。**

位置：[g33_mutation_gates.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g33_mutation_gates.py:42)、[test_g3_3_cas.py:793](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_3_cas.py:793)。

分别移除 **A3 锁**、**A3 CAS**，各跑现有两道增量门：**4/4 PASS**。等待门在 `:810` 等 holder 结束后才断言；无锁时增量块先完成，holder 随后追加，最终两段文本仍都存在。

七条变异还没有覆盖建板账本锁、主块两个 A2 CAS 发布点。建议补对应负控及确定性的读后修改、放锁前完成状态断言。

M1 主锁变异本轮确实打红；额外四次执行均因子进程 **CAS 冲突 rc=1**，在 `:160` 失败，未运行到 attempt 丢失断言。`:155` 连续启动没有读取屏障；[并发取证脚本:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g33_concurrency_evidence.py:100) 同样如此，不能保证任意调度下可靠撞窗。

**M3．60 ms 扫描门可被调度造成双向误判。**

位置：[test_g3_3_cas.py:676](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_3_cas.py:676)、同文件 `:730`。

本轮定向调度观测：

- 原生产锁不变，仅在 append 返回后、写 done 前延迟 150 ms：`remaining=155.40 ms`，测试 **FAIL，假红**。
- 真正施加 M7 丢锁变异，父探针第 30 次后暂停 1 s：`remaining=0.0577 ms`，测试 **PASS，假绿**。

20 万行和 `attempts>=20` 不能证明完整观察临界区。建议使用进程握手和明确暂停点，直接验证扫描、写入阶段仍持锁。

**M4．负控 SURVIVED 时，脚本仍可能以 rc=0 结束。**

位置：[g33_mutation_gates.py:253](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g33_mutation_gates.py:253)、同文件 `:265`。

用无效变异控制跑真实目标门，得到：

`SURVIVED，gate_rc=0，restore_identical=true，leftovers=[]，main_returncode=0`。

返回值只检查还原与残留。建议同时要求选择非空、无 ANCHOR-DRIFT、全部 KILLED。

`_failed_nodeids/:124` 和 `_hit/:134` 的身份匹配本身未发现兄弟测试喂饱：实测 `test_xy`、`test_x_other` 不命中，`test_x[1]` 命中，ERROR 不命中。但**指定门自身因调度或其他原因失败**仍会算 KILLED，M3 已证明这种风险。

## LOW

**L1．`flock` 选型理由与现有测试形态不符；实际共有五个持锁点。**

位置：[quiz-answer/SKILL.md:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:250)、[learning_event_log.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py:68)。

仓库搜索只找到 [test_g3_2_review_ledger.py:589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_2_review_ledger.py:589) 一处同进程 exec 主块；该测试未参数化，vault 为函数级 fixture。G3-3 使用子进程。实测 `flock`：旧 fd 仍持锁时第二个 fd 被阻塞；关闭旧 fd 后即可取得。**重复调用本身不会自锁。**

逐段核对结果：

| 持锁点 | 源码观察 |
|---|---|
| 主块 per-node，`:281` | 专用 `.lock` fd 不关闭；NODE、EV、临时文件不是该锁文件 |
| A3 per-node，`:122` | CAS 只重开 NODE，没有重开 `.lock` |
| 主块账本，`:2886` | 持锁段只用 `_fd`，最终 `:2902` 关闭 |
| 建板账本，`:452` | 扫描、写入只用 fd，最终 `:477` 关闭 |
| backend，`:159` | 单调用 `_read_all(fd)` 正确，但跨调用关闭仍有 H1 |

`lockf` 可以使用，但应修复生命周期，并改正选型理由；不能用 per-process 重入掩盖 fd 管理问题。

**L2．CAS 的“全文字节 sha256”描述不准确。**

位置：[fsrs_bridge.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/scripts/fsrs_bridge.py:190)、同文件 `:204`。

实测：

- 同内容替换文件：`cas_conflict=None`。
- `attempt_count: 1` 改成等价的 `"1"`：判冲突。
- LF 改 CRLF：**原始 SHA 改变，但 `cas_conflict=None`**。

原因是默认文本读取先规范化换行，再重新编码计算 SHA。等价格式改动被拒，是整份覆盖策略的保守选择；普通正文改动在检查前拒绝也合理。若承诺原始字节比较，应保留原始换行或直接使用 bytes。

**L3．“零写”与形态门的保障范围需要收窄表述。**

位置：[quiz-answer/SKILL.md:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md:280)、同文件 `:120`；[test_g3_3_cas.py:761](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_3_cas.py:761)。

空 event_id 实测 **rc=1、节点 SHA 不变、账本不存在，但新增一个 `.lock`**。锁目录在后续语义校验前创建；`.gitignore` 不会消除该写入。现有 `_write_face` 只能证明节点与账本范围，不能证明全文件系统零写。

形态门只禁止字面量 `open(EV`；向持锁段插入有效的 `open (EV, "rb").close()`，测试仍 **PASS**。别名、间接调用及首个 write 后的打开也不在其扫描范围。建议补运行期同 inode 锁探针。

A3 重算本身则核验通过：`:146` 每轮重置 `added`。一次冲突实测计数 `[1,0]`、最终回执 0；四次冲突为 `[1,0,0,0]`，payload 保留、没有 `.incr-tmp`、节点保持外部最新内容，仅产生锁文件。两块采取不同冲突处置是合理的；A3 的问题在 H6 的发布窗口及 M2 的测试覆盖。

**总体判断：不建议通过本 diff；普通回归和七条既选负控均通过，但已复现新增幂等回退、锁提前释放、乱序误标及短写成功误报，并确认新增并发防护仍有覆盖缺口。**


