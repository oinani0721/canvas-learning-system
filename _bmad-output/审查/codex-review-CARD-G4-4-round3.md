审查锚点：G4-4 提交态 `d5f27020`。审查期间分支被 OBS 车道推进到 `c1f8968d`，但 G4-4 代码、测试、UAT 和 evidence 字节未变，因此结论适用于当前 HEAD。

## Round-2 整改逐项复核

1. **PASS — B1 活性对照与 M8**

   6 条干扰数据确实把 `a_neighbor` 挤出主检索候选：[test_agentic_rag_vault_scope.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:370)。测试要求实际出现 `source_type=neighbor_expansion` 且扩展内容来自 A：[test_agentic_rag_vault_scope.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:521)。

   M8 将扩展替换为恒等赋值：[g44_mutations.py:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/g44_mutations.py:130)。我在 exact-HEAD 临时副本中复跑，目标门确实 `exit=1`；完整脚本 8/8 均由真实 pytest 失败杀死。

2. **FAIL（HIGH）— 跨 subject 登记没有完整成立**

   缺陷及根因登记正确：主检索传 `subject`，邻居扩展只按 `canvas_file LIKE` 查询整表：[nodes.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:397)、[lancedb_client.py:2250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/clients/lancedb_client.py:2250)。`--runxfail` 也真实复现 `PHYSICS_SECRET` 泄漏并在断言处失败：[test_agentic_rag_vault_scope.py:610](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:610)。

   但整改声称宽于证据：

   - marker 是 `xfail(strict=False)`，没有限定预期异常；意外修复会 XPASS 且 CI 仍成功，其他初始化异常也可被算作 XFAIL，不能称为 fail-closed“边界锁”：[test_agentic_rag_vault_scope.py:536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:536)。
   - 所谓 physics 行实际没有写入 `subject="physics"`，请求 ContextVar 也只有 vault 基组：[test_agentic_rag_vault_scope.py:550](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:550)、[test_agentic_rag_vault_scope.py:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:595)。
   - UAT 仍承诺“不把别的学科笔记混进答案”，却在后文声称已撤回这种声明：[UAT:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:38)、[UAT:176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:176)。
   - 权威未合卡台账没有该缺陷的 owner/卡号条目：[未合卡追踪台账.md:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:14)。不满足最终轮残留 HIGH 时“留台账、不合并”的规则：[W8-2.md:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W8-2.md:74)。

3. **PASS — HIGH-5 数字与局部声明修正**

   - `recommend_action` 确为 9 条本卡新增回归加 1 条开工前存量红；十处调用均已注入 `Response()`，当前 exact-HEAD 复跑 `40 passed`：[test_recommend_action.py:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_recommend_action.py:275)、[test_recommend_action.py:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_recommend_action.py:76)。
   - 两新文件确为 `35 collected = 34 passed + 1 xfailed`。
   - 4-B 已诚实限定为插件无 full-RAG 路径；§6.5 a/d 的响应头和独占面说明正确：[UAT:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:68)、[UAT:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:145)、[UAT:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:148)。

4. **FAIL（HIGH）— HIGH-6 收官裁判数字仍错误**

   `final-judge1.txt` 明写 `collected 80 items`，摘要为 `3 failed, 76 passed, 1 xfailed`，合计也是 80：[final-judge1.txt:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/final-judge1.txt:7)、[final-judge1.txt:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/final-judge1.txt:104)。UAT 却写成 79，并称与独立复跑一致：[UAT:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:55)。

   `99 passed` 是真实原始结果，但包含 4 条 OBS 测试：[final-judge2.txt:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/final-judge2.txt:7)、[final-judge2.txt:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/final-judge2.txt:13)。排除 OBS 后可比口径是 95；当前没有单独归档所称的 comm 输出。

5. **PASS — HIGH-4 历史记录及 8/8**

   UAT 已补 v2→v3 记录并改为 8/8：[UAT:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:125)。runner 只接受 `exit==1`，其他退出码明确失败：[g44_mutations.py:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/g44_mutations.py:145)。exact-HEAD 独立复跑确认 8/8。

## 新改动常规扫描

**HIGH — “邻居扩展与主链同源同表”仍是过宽声明。**

无 `course_id` 时该结论成立；但生产 `course_id` 分支主检索使用 `vault_notes`，邻居扩展却固定使用 `canvas_nodes`：[nodes.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:381)、[nodes.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:419)。现有真库门的 state 没有 `course_id`，未覆盖此分支：[test_agentic_rag_vault_scope.py:427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:427)。

因此 UAT 无条件声称“统一到主链同表”不成立：[UAT:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:105)、[UAT:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:150)。

验证限制：未跑全量 CI、真实 LangGraph/LLM、真实 Vault/Neo4j 或 `test_agents_dedup.py`；未提交或修改任何项目文件。

**总结论：REJECT。**


