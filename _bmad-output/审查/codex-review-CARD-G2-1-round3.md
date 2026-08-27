总体结论：**不可接收**。指定整改多数已落地，但扫尾发现 **1 个新的 BLOCKER false-green**；当前分布只能机械复算，不能作为语义正确的终审结果。

1. **BLOCKER-1 五处降级 — PASS**

   `question_generator:985`、`recommendation:213/246/300`、`verification:2151` 均已改为 `R1:partial / CONDITIONAL`（[审计表:109](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:109>)、[113](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:113>)、[118](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:118>)）。源码确分别存在未过滤的 `r`、匿名端点、变长路径中间节点或关系（[question_generator.py:970](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/question_generator.py:970>)、[recommendation_service.py:205](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:205>)、[230](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:230>)、[290](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:290>)、[verification_service.py:2135](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/verification_service.py:2135>)）。

   R1 正例也已正确换为 `targeting_material_service.py:163`：`n/e/m` 三侧均严格等值过滤（[源码:165](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/targeting_material_service.py:165>)）；读契约同时诚实注明 verification 的 `r` 缺口（[读契约:33](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:33>)）。

2. **判定分布 — 机械 PASS，语义 FAIL**

   逐行机械复算：

   - §3：`45 / 6 / 14 / 6 / 4`
   - §4：`10 / 10 / 1 / 0 / 3`
   - A/B 99 行合计，按报告顺序 `COMPLIANT/CROSS/CONDITIONAL/NON-QUERY/VIOLATION`：`55/16/15/7/6`

   但下述新 false-green 至少应由 COMPLIANT 降为 CONDITIONAL，因此语义分布最低应为：

   - §3：`44/6/15/6/4`
   - A/B：`54/16/16/7/6`

3. **BLOCKER-2 edge_client:436 — FAIL**

   核心判定已升为 `R1:violation(R3 不适用) / VIOLATION`，这部分 PASS。源码确实只有 Node ID／可选 canvas path，无 group scope（[neo4j_edge_client.py:419](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_edge_client.py:419>)），且 Canvas node ID 可外传或仅取 UUID 前八位（[canvas_service.py:792](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/canvas_service.py:792>)）。

   但审计同一 note 仍保留旧句“R3 node id 点查免 group 过滤”，随后又称其属于 R3 反例；该矛盾在 §3 与 §7 各出现一次（[审计:61](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:61>)、[264](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:264>)）。核心 blocker 已关闭，但“理由一致”未通过。

4. **MEDIUM 物理化列 — PASS**

   `memory_service:1697` 与 `graphiti_belief_service:132` 均已改为 `conditional (sanitize 不做 legacy canonicalization)`（[审计:90](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:90>)、[107](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:107>)），与 `sanitize_group_id_for_graphiti()` 对 `vault:` 会物理化、对 `cs188` 原样直通的实现相符（[group_id_compat.py:64](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/graphiti/group_id_compat.py:64>)）。

5. **MEDIUM migration advisory — PASS**

   两行已改为 `R2:ok(docstring)` / `W4:ok(docstring)`，并明确装饰器只是 advisory（[审计:136](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:136>)）。与 R2/W4 的 docstring 最低线一致。

6. **LOW 指定项 — PASS**

   §7 CONDITIONAL 标题已改为多风险面表述（[审计:268](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:268>)）；§5 #15 已明确“外部传入、uuid4 来源不可证”（[审计:172](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:172>)）。

7. **剩余 COMPLIANT 扫尾 — FAIL，新增 BLOCKER**

   `exam_service_ext.py:148` 仍判 `W1/W5:ok / COMPLIANT`（[审计:75](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:75>)），但源码只给 `src/tgt` 加 group：

   - `MERGE ...[r:EXAM_DISCOVERED {relation_type}]...`
   - 随后才 `SET r.group_id = $group_id`

   见 [exam_service_ext.py:138](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/exam_service_ext.py:138>)。端点过滤不能证明存量 `r.group_id` 与端点一致；错组或 NULL 关系仍可能被 MERGE 命中并覆写。按本审计对“关系不跨组前提不可证”的严格口径，最低应降 `W1/W5:partial / CONDITIONAL`。

   因此 [审计:329](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:329>) 把它列作“读侧全覆盖正例”也不成立；纯 R1 正例应只保留 targeting_material。

残留分级：

- **BLOCKER 1 类**：`exam_service_ext:148` 关系身份 false-green。
- **HIGH 0**
- **MEDIUM 1 类**：交接链仍写 `CONDITIONAL 10`，与当前表的 15、修正后的最低 16 均不符（[审计:291](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:291>)）。
- **LOW 4 类**：edge R3 旧句；question_generator 残留“模范实现”；recommendation:246 漏记未过滤的 `live` 关系；learning_context:387 已为 CONDITIONAL，但 note 漏记未过滤且被返回的 `r.reason/r.label`。

本轮仅静态读取，未修改文件，未运行测试或业务代码。既有对抗审计规范促使本轮采用并行独立复核、源码优先，并将作者整改记录仅视为索引而非证明。


