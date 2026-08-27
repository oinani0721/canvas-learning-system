结论：**FAIL，不建议接收 CARD-G2-1 当前交付物。** 核心原因是出现了跨 vault 契约的 false-green，且 §5 汇总/交接不可复算。审阅基于分支 `card/n6-contract`、HEAD `b47ebfba351f3eedb496a97961083c5e3b1d5df7`；全程只读，未运行测试或业务代码。

## BLOCKER

1. **R1 的逐 alias 要求与实际 COMPLIANT 判定冲突，产生安全相关 false-green。**

   R1 明文要求每个可能跨 vault 的节点/关系 alias 都过滤，[读契约:23-34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:23)。但：

   - §5 #2 判 `R1:ok`，[审计:159](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:159>)；实际只过滤 `c.group_id`，未过滤带 group 属性的 `r:LEARNED`，[源码:823-839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_client.py:823)。
   - profile 三条查询也只过滤 `n`；清单甚至承认 `e/r` 未过滤，却仍判 COMPLIANT，[审计:48-50](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:48>)、[源码:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/api/v1/endpoints/profile.py:214)。

   在契约补充并证明“关系绝不跨组”的例外之前，这些至少应判 CONDITIONAL，不能进入 COMPLIANT 统计。

## HIGH

1. **R3/W2/W5 的“全局唯一 ID”口径自相矛盾，并放行实际不可证明全局唯一的 ID。**

   R3 把 `edge_id`、`association_id`、Canvas node `id` 列为免 group 示例，[读契约:40-42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:40)。但 `edge_id` 可退化成端点拼接值，[neo4j_edge_client.py:165-168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_edge_client.py:165)；Canvas node ID 可由外部传入，缺失时仅取 UUID 前 8 位，[canvas_service.py:792-794](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/canvas_service.py:792)。

   同时，W2 允许 UUID 点删，却又把自称 UUID 的 `association_id` 判 violation；W5 对同一 ID 点更也作 violation，[写契约:36-54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:36)。应先建立每类 ID 的生成与唯一性证明，再统一三条规则。

2. **§5 汇总算术错误，且 G2-3 交接漏项。**

   #16 明列 `W5:violation`，[审计:173](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:173>)；但汇总漏掉它，并把表外、在 §4 明确判 CONDITIONAL 的通用代理算成第二个 COMPLIANT，[审计:132、178](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:178>)。

   按表内当前标注应为 **17 violation / 1 conditional / 1 compliant**。G2-3 交接又只列 W1 五处和 W2 两处，[写契约:56-59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:56)，未接住 #16；两条 xfail 也只调用 `create_learning_relationship`，[门测试:318-351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:318)，不能作为其余六处修复的门。

## MEDIUM

1. **两条 strict xfail 的交接文字清楚、`strict` 语义正确，但可能因错误原因 XFAIL。**

   reason/docstring 已明确“修复后 XPASS(strict) → 移除标记”，[门测试:15-19、302-307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:15)。`strict=True` 确实会让 XPASS 令 suite 失败，[pytest 官方文档](https://docs.pytest.org/en/stable/how-to/skipping.html)。

   但 marker 覆盖整个测试且未限定预期失败；写入失败、查询异常或 `assert ok_a and ok_b` 失败也会被接受为 XFAIL，[门测试:310-335、338-362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:310)。因此“准确复现 W1”只能判 PARTIAL。

2. **`memory_service.py:1697` 的 `R5:ok/physical=yes` false-clean。**

   实际绑定链只调用 `sanitize_group_id_for_graphiti()`，[memory_service.py:1552-1557](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/memory_service.py:1552)；该函数会让 legacy `cs188` 原样通过，[group_id_compat.py:64-87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/graphiti/group_id_compat.py:64)。只有 `to_physical_group_id()` 执行 legacy canonicalization，[同文件:140-185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/graphiti/group_id_compat.py:140)。与 R5 MUST 不符，应至少是 `R5:partial/physical=conditional`，而非 clean COMPLIANT。

3. **跨 vault 声明规则不可一致复算。**

   W4 允许“装饰器或等价 docstring”，[写契约:48-50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:48)；迁移函数已有明确迁移、生产写与 dry-run 说明，[group_id_migration_service.py:124-146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/group_id_migration_service.py:124)，清单仍标 `W4:needs-decorator`，[审计:137](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:137>)。应明确究竟“装饰器强制”还是“docstring 足够”。

## LOW

1. `fallback_sync_service.py:458` 的核心 VIOLATION 正确，但 `physical=yes` 与同一行 `W3:conditional` 及条件绑定矛盾，[审计:88](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:88>)、[源码:458-465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/fallback_sync_service.py:458)。

2. 读契约称 helper 两项局限“见审计 §5”，[读契约:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:15)；实际位于审计 §2，[审计:21-37](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:21)。

## 抽样对账

§3/§4 分层抽取 8 处：**5 PASS / 2 PARTIAL / 1 FAIL**。

| 抽样 | 结果 | 源证据 |
|---|---|---|
| exam_sessions:175 COMPLIANT | PASS | [153-175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/api/v1/endpoints/exam_sessions.py:153) |
| neo4j_edge_client:370 CONDITIONAL | PASS | [342-370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_edge_client.py:342) |
| fallback_sync_service:458 VIOLATION | PARTIAL | [442-465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/fallback_sync_service.py:442) |
| graphiti_belief_service:108 CROSS-VAULT | PASS | [105-113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/graphiti_belief_service.py:105) |
| memory_service:1697 COMPLIANT | FAIL | [1681-1700](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/memory_service.py:1681) |
| neo4j_client:450 CONDITIONAL | PASS | [419-452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_client.py:419) |
| group_id_migration:225 CROSS-VAULT | PARTIAL | [201-225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/group_id_migration_service.py:201) |
| sync_service:578 COMPLIANT | PASS | [578-605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/sync_service.py:578) |

§5 抽 4 条：#1 PASS；#2 FAIL（R1 false-green）；#4 PARTIAL（CONDITIONAL 成立但漏记 `c` 未过滤）；#15 FAIL（UUID scope 理由自相矛盾）。四条源代码行号均准确。

铁律 D 在首次快照中为 **PASS**：`backend/app`、`neo4j_client.py`、`cypher_helpers.py` 均零 diff；tracked diff 只有 [.gitignore:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.gitignore:46) 新增规则目录豁免，其余为 md/测试。审阅期间 worktree 出现另一批 retrieval/G4-12 并发改动，无法归因 G2-1，因此当前全树 dirty status 不宜作为本卡纯净性证据。

总体而言，根 CLAUDE.md 的冲突、生产 helper 调用为 0、helper 两项局限均记录属实；但核心分类契约尚不自洽，且随机抽样已出现 false-green。应修订规则口径、重算 §3/§5 分类与汇总、收窄 xfail 失败原因后再接收。


