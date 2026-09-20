> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-CARD-STATES-ATOMIC-WRITE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-CARD-STATES-ATOMIC-WRITE-r2.md)"`
> 审查绑定: `d7ab47c811230989765cb65568ff6b6b15ea7b7e`（当时 HEAD；本轮整改后 HEAD 已前进，故本份**不绑最终 HEAD**，由 round-3 绑）
> 会话头自证（抄 `.stderr`，括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`
> 判定: BLOCKER=0 HIGH=1 MEDIUM=5 LOW=0

---

**整改部分成立，但原 HIGH 不能关闭。** 本轮全程只读；下面的“未被拦下的输入”均为静态推导，未运行修改后的实现。

1. **HIGH — 单进程取消后，仍可能共享同一个 inode，发生交叉截断、覆盖或删除。**  
   位置：[review_service.py:716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:716)、`:728`、`:1048`。

   inode 认领确实挡住了“**A 已 replace → B 新建不同 inode → A 清理**”这一条路径。但 B 若在 A replace **之前**执行 `open(tmp, "wb")`，会截断既有文件，A/B 记录的是同一个 inode。

   **复现思路：**让 A 停在 open/fstat 之后、write 之前，取消 A 协程；B 获锁并完成写入、replace、返回 True；A 线程恢复后，其原句柄仍能把旧内容写进已经成为目标文件的 inode。另一种未被拦下的输入是 B 尚未 replace 时 A 的 fsync 失败，A 清理会因 inode 相同而删除 B 正在使用的 tmp。

   因此，剩余截断风险不能只登记为“跨进程／多 worker”。`stat→unlink` 的 TOCTOU 也仍存在，但允许读取面没有调用频率、取消率等数据，不能据此断言可忽略；上述共享 inode 路径更值得优先处理，因为它不依赖极窄窗口。TOCTOU 不另计一项。

2. **MEDIUM — 新增认领步骤确实引入了自身 tmp 未清理的路径。**  
   位置：[review_service.py:677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:677)、`:680–682`、`:717`。

   **复现思路：**文件 fsync 失败后，让清理中的 `os.stat(tmp)` 抛非 `FileNotFoundError` 的 `OSError`；即使 tmp 存在且属于本次，也会静默跳过 unlink。另一个输入是 open 已创建 tmp，而紧接着的 fstat 失败，此时 `tmp_ino=None` 同样跳过清理。

   所以 `:678`“文件根本没建出来”的推断不成立。保守地不删未知归属文件有其理由，但不能同时宣称每条路径都会尝试删除、认领错误不会被吞掉。

3. **MEDIUM — 新增文件 fsync 失败门，仍没有绑定整个写阶段的清理覆盖及 flush 顺序。**  
   位置：[test_g3_7_truth_source.py:1019](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1019)、`:1030`；实现 `review_service.py:715–720`。

   **复现思路：**把 open/fstat/write/flush 放在清理 `try` 外，只从文件 fsync 开始覆盖；11 条门按代码推导仍可全绿，但实际 write/flush 失败会残留。

   更小的未被拦下的输入是仅删除 `fh.flush()`：这些小快照仍会在退出 `with` 时写出，最终内容断言通过，却让文件 fsync 发生在缓冲数据写出之前。新增门已绑定“文件 fsync 失败”，尚不能代表所有写阶段失败。

4. **MEDIUM — 目录 fsync 门只绑定调用序号，没有绑定目录身份。**  
   位置：[test_g3_7_truth_source.py:1092](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1092)、`:1106`；实现 `review_service.py:722`。

   **复现思路：**仅将 `os.open(target.parent, …)` 改成 `os.open(target, …)`；第二次 fsync 变成同步普通文件，11 条门按代码推导仍可全绿，父目录却从未 fsync。

   `len(seen)==2` 因而不够。它也可能误红：正确实现若增加一次发布前的文件 fsync，探针会在第二次**文件** fsync 注入失败，随后“目标已经发布”的断言失败。应按 fd 对应的对象及发布顺序判断，不能把“第二次”直接等同于“目录”。

5. **MEDIUM — spec 仍存在无条件承诺及 Scenario 间冲突。**  
   位置：[spec.md:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:21)、`:62`、`:84`、`:150`。

   **复现思路：**现有 foreign tmp 门已经反驳 S1 `:84`“成功后不存在任何 tmp”；在同一输入中再让目录 fsync 失败，又会反驳新增 S7 `:150`“自身 publish 成功所以返回 True”。

   Requirement 逐句对照如下；关联到前述功能问题的内容不重复计数：

   | spec 行号 | 对照结果 |
   |---|---|
   | 8–12 | 正常串行路径的全量快照、JSON 参数吻合；取消交错受 HIGH 影响。 |
   | 14–20 | 当前代码的预编码、flush、文件 fsync、replace、目录 fsync及一次线程派发吻合。 |
   | 21–24 | 仍写“失败后无自身残留”；stat/fstat 输入不满足，认领错误也被静默吞掉。 |
   | 25–29 | 不同 inode 的指定路径受保护；inode 相同不等于仅本次使用。没有直接写目标路径，也不足以保证取消交错下目标不变。 |
   | 31–36 | 词法上位于锁内，但取消后线程 I/O 可继续在锁释放后执行。 |
   | 38–43 | 所示 fail-closed 分支确实在 try、mkdir 前返回。 |
   | 45–53 | 正常等待完成时，异常归一、回滚／保留内存及 pending dirty 行为吻合；取消不属三类异常。 |
   | 55–60 | 所示 dirty key 使用 vault/concept 二元组。 |
   | 62–68 | “replace 成功即清标记”失真；实际还须后续目录 fsync、close 等成功。后面的“不恢复丢失值”说明吻合。 |
   | 70–73 | 投影与调度真相源的区分吻合；所有调用方是否分别报告，超出本次读取面。 |

   对锁死文字仅指出失真，不评价该不该修改。

6. **MEDIUM — 最终 HEAD 的验收证据仍未闭合。**  
   位置：[dir-regression-r2-20260918T180241.txt:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-card-states-atomic/dir-regression-r2-20260918T180241.txt:7)。

   **复核思路：**逐份检查最终摘要、进程退出码、实际命令、SHA，以及执行前后源码绑定，不能用文件名或时间戳代替。

   | 存档 | 实际可确认的内容 |
   |---|---|
   | `dir-regression-r2-…180241.txt:7,45` | collected 1931；多次读取仍在增长，末次采样显示约 32% 进度，无最终摘要或 pytest 总退出码。`:38–43` 的 rc 是内部用例打印。 |
   | `suites-r2-…180241.txt:63–64` | **154 passed、10 warnings、rc=0**；没有 skipped 项，但没有命令或最终 SHA 绑定。 |
   | `unit-r2-*.txt` | 未找到匹配文件。 |
   | `ast-after-head-…174211.txt:3,9,14` | helper 为旧位置 `660–696`，明显不是当前 `685–729` 的认领整改结构。 |
   | `ast-falsification-anchor-…170355.txt:3–12` | 记录了旧实现的两个 to_thread、无 encode/helper；rc=0 表示提取成功，文件本身未记录裁判判红结果。 |
   | `ruff-…173940.txt:1,7` | 明写 **HEAD=7a5081f1**，检查通过不能绑定本轮 d7ab47c。 |
   | `pyright-r2-…180019.txt:1–2` | **0 errors、80 warnings、rc=0**；缺命令、检查范围和 SHA。 |

   仍缺稳定结束的目录级结果、passed/skipped 分列、实际命令，以及 `d7ab47c…` 与执行前后源码状态的绑定。

三段**负控输入各只拆了一层**，存档结果与自述一致：

| 负控输入 | 拆除内容 | 存档结果 |
|---|---|---|
| r2-1 | 清理动作 | 2 failed / 9 passed，rc=1；两条残留门红 |
| r2-2 | 文件 fsync | 3 failed / 8 passed，rc=1 |
| r2-3 | inode 认领条件 | 1 failed / 10 passed，rc=1；仅 foreign tmp 门红 |

三个 `sha-before` 内容一致，但未找到对应 `sha-after`。这不否定记录中的失败结果，却留下恢复状态的证据缺口。

**对照输入存档只运行了旧的 8 条门**：`redbind-ctrl-…174016.txt:7,112–113` 为 8 selected、3 failed / 5 passed、rc=1，不能当作本轮 11 条的结果。三个新增门在 `9c4e7e82` 形态下的静态判断是：

- `write_phase_failure…`：红，旧实现不调用 fsync，保存返回 True。
- `cleanup_spares_a_foreign_tmp`：**绿**，旧实现没有后续清理，会保留植入的 tmp。它绑定的是相对 round-1 无条件清理的整改，仍有防止回归的价值。
- `directory_fsync_failure…`：红，旧实现不调用 fsync，保存返回 True。

两个指定 diff 中新增 `type: ignore`、`pyright:`、`noqa` 均为 **0**，也没有配置文件变更。因此“本卡新增 ignore=0”属实，没有证据支持靠新增 ignore 掩盖错误；但两行 pyright 存档不足以证明最终 HEAD 的目标文件确实在检查范围内。

S3 的写模式 open 探针和 S1 的 `os.replace` 文案整改成立；本轮没有另列 LOW。

BLOCKER=0 HIGH=1 MEDIUM=5 LOW=0
