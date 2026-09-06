**整体判定：PARTIAL。发现 1 项 HIGH、2 项 MEDIUM、2 项 LOW；未确认 BLOCKER。** 本次仅阅读与重算证据，未运行 canary、变异或数据库操作。两份被审源码的 SHA-256 均与证据绑定一致；复核期间 HEAD 已由外部操作改变，以下结论绑定文件内容。

1. **HIGH — 前序 Neo4j 清理遮蔽了 Graphiti 删除路径，整体清理通过不能证明 Graphiti 删除接口承重。**

   **位置与事实：** [canary:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:483) 按 `group_id` 删除所有节点，没有业务 label 限制；[canary:727](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:727) 先执行它，再调用 Graphiti 删除。报告中的业务物理组与 Graphiti 组相同，见[身份记录:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/canary-normalized-20260905T093657Z.json:4)。因此正常路径已经提前清空 Graphiti 节点，随后逐节点删除可能没有对象可处理。

   M3 也没有补足这个缺口：其指定目标只要求 B 计数发生变化，业务节点的损失已足以令目标翻红。Graphiti 删除是否有效不会改变这项 KILLED 判定。

   **处置：** 为 Graphiti 删除建立独立的删前存在、实际删除及删后隔离证据。补证前，结论限定为“组合清理后的计数隔离”。

2. **MEDIUM — 五条变异的目标绑定正确，但不足以证明“每条判据均已验伪”，尤其缺 Graphiti 哨兵的翻红证据。**

   **位置与事实：** [MUTATION_SPECS:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:186) 的 `expect_red` 去重后仅覆盖 **4/12** 个 verdict，另有 M4 形状异常门。[裁判代码:970](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:970) 确实要求所有点名目标存在且严格为 `False`；[变异报告:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/canary-verify-judges-20260905T093952Z.json:17) 与之吻合，未发现点错目标。

   `outside_read_scope` **不是代码层面的恒零**：[canary:547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:547) 会对返回但不属于当前作用域的节点计数。然而现有变异没有证明它实际翻红。它也只能检查“返回记录没有越界”，不能证明没有漏返，因此不足以支持注释中“两套读口径没有分叉”的完整等价说法。

   **处置：** 收窄“每条判据”与“口径等价”的表述，补 Graphiti 哨兵的定向证据，并保存完整阶段计数和 verdict 矩阵。

3. **MEDIUM — `(c)` 的 3/3 KILLED 没有绑定指定失败断言。**

   **位置与事实：** [FSRS 变异裁判:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/g29_fsrs_test_mutations.py:32) 关闭 traceback，只保留测试摘要；[第46行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/g29_fsrs_test_mutations.py:46) 把任何非零退出码都判为 KILLED。[现有输出:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/fsrs-test-mutations-20260905T174346.txt:6) 只能证明三次均出现测试失败，不能证明失败来自预期断言。

   另外，C1 改变的是测试辅助函数读取哪个 state 文件，并未改变生产 runner 的 state 写入行为。其覆盖结论应据此限定。文件恢复则没有发现问题：本次原始字节 SHA 与历史绑定完整一致。

   **处置：** 将裁判绑定预期测试、失败位置和原因，保存对应失败输出，并区分观察器变化与生产行为缺陷。

4. **LOW — Markdown 投影缺失时，交叉排除断言会空串假通过。**

   **位置与事实：** [测试:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g29_dual_vault_fsrs_isolation.py:63) 把不存在的投影文件读成空串；[测试:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g29_dual_vault_fsrs_isolation.py:113) 随后只检查异库标识不在其中。JSON 有直接读取，state 有存在性检查，Markdown 没有对应前提。

   **处置：** 在排除异库内容之前，要求 Markdown 存在且包含预期的本库内容。现有摘要不足以确认历史运行中该文件实际生成。

5. **LOW — `NEGCTL_REJECTED_SOURCE` 的行号是固定标签，不是实际异常位置。**

   **位置与事实：** [canary:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:274) 捕获所有 `RuntimeError`，统一标注 guard 的同一抛错分支；但 guard 另有[白名单冲突:893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/support/live_port_guard.py:893) 和[解析失败:903](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/support/live_port_guard.py:903) 分支。

   **处置：** 将固定来源限定为函数身份，或记录真实拒绝分支。**本次四条端口负控实际都对应所标分支，没有发生错归因。**

其余重点问题的核对结果：

- **装门时机：显式顺序通过，完整传递导入链读取面不足。** [canary:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:52) 开始只有显式标准库导入，随后导入 guard 并在第79行装门；[guard:594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/support/live_port_guard.py:594) 确实先检查已加载的 `uvloop`。但给定范围不含 guard 顶层导入及相关辅助实现，不能确认其全部间接导入，也不能据此证明整个启动窗口没有出站行为。

- **七条负控：均有正确的当前归因。** [调用顺序:1103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:1103) 是先 URI、后路径；[负控记录:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g29/canary-negctl-20260905T173916.txt:5) 中前四条理由对应端口白名单分支，后三条对应路径检查，全部 rc=2。未见路径先拒却归给端口门。它们证明前置拒绝，不是实际 socket 拦截。

- **Graphiti 交叉查询确实覆盖 Graphiti 对象。** [写入:498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:498) 调用 EpisodicNode／EntityNode 的 `save`，[读取:539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:539) 调用各自的 `get_by_group_ids`，没有用业务 Concept 代替。第三方方法内部实现不在读取面内。

- **规范化报告不是空壳。** 按[normalize:1056](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:1056) 独立重算，两份结果与保存文件完全一致，两文件也字节相同。保留下来的承重内容包括：两套身份、10 个阶段共100个计数／哨兵值、Concept 两组物理分布、12个 verdict，以及附带删表发现。原始报告实际只有时间、耗时、临时路径不同。删除 `guard_summary` 意味着空 diff 本身不证明端口安全；两份独立账本仍需单独判断。

- **B 删前快照真实；保留共享 User 不会使比较恒真。** [canary:867](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/scripts/g29_dual_vault_canary.py:867) 在清理 A 前保存 B 的新计数字典，删后重新读取，没有原地覆盖快照。生产[写入:1021](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/app/clients/neo4j_client.py:1021) 确实共享 User，但 Concept／LEARNED 按组区分；B 的关系损失仍会令判据变红。这个取舍保住了当前计数判据，但“A 已清空”只能指被计数的资产，不能扩写成所有关联节点均删除。共享 User 是否有正式设计裁决，读取面不足。

已登记的 LanceDB 初始化跨 vault 删表发现，与给定源码及报告一致，按边界继续移交，不要求本卡修改生产代码。

**整体结论：主要计数、交叉读取和删前快照有证据支撑，但 Graphiti 删除覆盖与“全部判据已独立验伪”的结论尚未闭合。**


