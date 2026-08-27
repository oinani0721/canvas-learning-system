总体结论：**不可接收**。8 项整改结果为 **4 PASS / 4 FAIL**；仍有 **2 类 BLOCKER false-green**。按要求仅静态读取，未运行测试或业务代码。

1. **BLOCKER（部分 alias）— FAIL**

   指定整改均已落地：五行已降 `CONDITIONAL`（[审计:48–50](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:48>)、[90](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:90>)、[107](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:107>)）；§5 #2 已降级（[审计:159](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:159>)）；R1 已补“部分 alias = CONDITIONAL”（[读契约:35](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:35>)）。

   当前标签机械复算确为 `61/16/10/7/5`，但仍至少有五个同型 `COMPLIANT` false-green：

   - `question_generator.py:985` 的关系 `r` 未过滤（[源码:970](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/question_generator.py:970>)；[审计:109](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:109>)）。
   - `recommendation_service.py:213/246/300` 的关系、匿名端点及变长路径中间节点未完整过滤（[源码:205](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:205>)、[230](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:230>)、[290](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/recommendation_service.py:290>)；[审计:113–116](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:113>)）。
   - `verification_service.py:2151` 返回 `r.label`，但未过滤 `r.group_id`（[源码:2135](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/services/verification_service.py:2135>)；[审计:118](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:118>)）。

   仅修正这五行，分布就应至少变为 `COMPLIANT 56 / CONDITIONAL 15`，因此当前分布仅“算术一致”，不满足新 R1 的语义。

2. **HIGH-1（ID 口径）— FAIL**

   R3、W2、W5 的文字已统一为服务端 uuid4 来源可证（[读契约:43–52](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:43>)、[写契约:36–42](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:36>)、[54–58](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:54>)）。

   但审计仍把 Canvas/Node `id` 点查判为 `R3:ok / COMPLIANT`，同一行还承认复制 canvas 会撞 ID（[审计:61](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:61>)；[源码:419](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/clients/neo4j_edge_client.py:419>)）。这与 R3 明列的 Canvas node ID 反例直接冲突，构成新的 BLOCKER false-green。

   §5 #16 自洽；#15 verdict 为 `W2:violation`，但说明仍写“uuid 点删，勉强够 ID-scope 线”（[审计:172–173](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:172>)），与新 W2 理由冲突。

3. **HIGH-2（汇总与交接）— PASS**

   独立复算：`VIOLATION={#1,#3,#5–#19}=17`，`CONDITIONAL={#2,#4}=2`，`COMPLIANT=0`（[审计:156–184](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:156>)）。写契约及审计交接均补 #16，并明确两条 xfail 只覆盖 #1（[写契约:60–63](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:60>)、[审计:282–285](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:282>)）。

4. **MEDIUM-1（xfail 原因收窄）— PASS**

   两条 marker 均有 `raises=AssertionError`（[测试:312](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:312>)、[344](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:344>)）；写入前置条件统一经 `pytest.fail()`（[测试:301–309](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/integration/test_cypher_contract_gate.py:301>)）。

5. **MEDIUM-2（R5 false-clean）— FAIL，残留 LOW**

   核心 verdict 已降 `R5:partial / CONDITIONAL`，但 `memory_service:1697` 与 `graphiti_belief_service:132` 的“物理化”列写成 `no`，而同一行说明承认规范 `vault:` 输入会被 sanitize 成物理格式、仅 legacy 值不 canonicalize（[审计:90、107](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:90>)；[转换实现:64、140](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/app/graphiti/group_id_compat.py:64>)）。该列应为 `conditional`。

6. **MEDIUM-3（跨 vault 声明口径）— FAIL，残留 MEDIUM**

   R2/W4 规则已统一为“docstring/注释为最低线，装饰器仅推荐”（[读契约:41](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:41>)、[写契约:52](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-write-contract.md:52>)），但审计迁移行仍写 `R2/W4:needs-decorator`，甚至称“W4 要求装饰器”（[审计:136–137](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:136>)），与新规则及 §7 的 advisory 重解释不一致。

7. **LOW-1（fallback physical 列）— PASS**

   `fallback_sync_service.py:352/458` 两行均已改为 `conditional (group_id 为空时原样传递)`（[审计:87–88](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:87>)）。

8. **LOW-2（错误章节引用）— PASS**

   读契约已由 §5 改为 §2（[读契约:15](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/.claude/rules/cypher-read-contract.md:15>)），与审计实际位置一致。

残留分级：**BLOCKER 2 类 / HIGH 0 / MEDIUM 2 类 / LOW 3 类**。另一个 LOW 是 §7 标题仍把全部 CONDITIONAL 称作“R4 静默退化风险面”，实际已混入 R1/R5 条目（[审计:267](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md:267>)）。
