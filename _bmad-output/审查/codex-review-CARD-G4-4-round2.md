审查锚点：`card/w8-scope`，`HEAD=c9d8c0f613ed`。目标文件与 HEAD 字节一致；并发生成的未跟踪 Round-2/OBS 输出未作为证据。

## Round-2 逐项复核

1. Round-1 BLOCKER-1 — FAIL（HIGH）

   窄义代码修复成立：邻居扩展现传入已解析的 `canvas_nodes`，客户端直接打开该解析后表名：[nodes.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:419)、[lancedb_client.py:2240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/clients/lancedb_client.py:2240)。

   但声称的 `a_neighbor` 活性对照是假绿：它本来就在仅三行的主检索表中：[test_agentic_rag_vault_scope.py:311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:311)。将 `expand_neighbors` 运行时替换为恒等函数后，结果仍含 `a_neighbor` 且不含 `b_secret`，所以 [测试的三项断言](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:482)全部通过。M6 能杀“退回裸 `vault_notes`”，但不能证明扩展链仍活着。

2. Round-1 BLOCKER-3 — PASS

   A/B 前缀表和裸 legacy 表确实在同一 tmp LanceDB 中创建：[test_agentic_rag_vault_scope.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_agentic_rag_vault_scope.py:303)。API 测试明确不证明真实检索/全图：[test_rag_vault_scope_api.py:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_rag_vault_scope_api.py:26)；验收单也明确撤回全 LangGraph 结论并披露 B0.7：[UAT:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:149)。

3. Round-1 HIGH-2 — PASS

   模型层拒绝空白：[rag.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/api/v1/endpoints/rag.py:63)。三种空白形态含全角空格均断言 422 和服务零调用：[test_rag_vault_scope_api.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_rag_vault_scope_api.py:125)。

4. Round-1 HIGH-4 代码适配 — PASS

   十处直调均注入 `Response()`，例如 [test_recommend_action.py:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_recommend_action.py:275)；`RuntimeError` 与生产捕获集一致：[test_recommend_action.py:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_recommend_action.py:76)、[agents.py:2160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/api/v1/endpoints/agents.py:2160)。当前文件 40/40 通过。

5. Round-1 HIGH-4 理由、数字、覆盖面 — FAIL（HIGH）

   - `ca116f51^` 独立复跑为 `39 passed, 1 failed`；裸 `Exception` 用例开工前已红。因此签名变更新增的是九条失败，不是验收单声称的十条“本卡回归”：[UAT:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:114)。
   - 两新文件实际为 API 18 + unit 16 = 34，不是 API 19 + unit 14 = 33：[UAT:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:63)。
   - 4-B 的“正常 Obsidian 对话验证本卡”不会触达本卡链路：[UAT:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:68)。插件的 `agents/dialog` 已删除：[main.ts:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/frontend/obsidian-plugin/src/main.ts:360)，插件 full-RAG 路径仍未实现：[SKILL.md:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/canvas-vault/.claude/skills/chat-with-context/SKILL.md:52)。

6. Round-1 HIGH-5 偏差表 — FAIL（HIGH）

   a/b/c/e/f 的核心映射基本正确，但 d 行仍把三个测试文件加生产文件 `rag.py` 写成“四个测试文件”，并称都不在独占面：[UAT:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:129)；卡文明定 `rag.py` 属独占面：[W8-2.md:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W8-2.md:77)。a 行“客户端不可见”也不准确：响应头只是未进入 OpenAPI/schema，HTTP 客户端仍可读取。

7. Round-1 HIGH-6 交付完整性 — FAIL（HIGH）

   新测试、UAT、round-1 存档均已 tracked；提交归属和 `78c9e6e7 → aaecf696` 时序正确。但验收单声称收官裁判输出已归档：[UAT:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:55)，实际没有 `aaecf696` 后的裁判 1/2 输出。当前隔离 HEAD 实跑：

   - 四文件：`79 collected, 76 passed, 3` 条同样存量红，不是 `74+3`。
   - API 裁判排除 OBS/dedup：`95 passed`；现存 `after-judge2-v2.txt` 仍是整改前的 `92 passed + 3 OBS failed`。

8. Round-1 HIGH-7 变异证据 — PASS

   v2 仅接受 `exit==1`：[g44_mutations.py:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/g44_mutations.py:130)；M5/M6/M7 是实际变异：[g44_mutations.py:99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/evidence-g44/g44_mutations.py:99)。隔离 HEAD 独立执行得到 7/7 `exit=1`，runner 最终 `exit=0`，三目标文件还原一致。

## 新改动面发现

HIGH — 邻居扩展绕过 `subject_id`

主检索把 `subject` 转成 WHERE 条件：[nodes.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:397)、[lancedb_client.py:3122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/clients/lancedb_client.py:3122)；邻居扩展却不传 subject，只按 `canvas_file LIKE` 查整张 vault 表：[nodes.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/nodes.py:419)、[lancedb_client.py:2250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/clients/lancedb_client.py:2250)。

真实 tmp LanceDB 生产节点反例：

`VaultScope=vault:vault_a:math`、`subject=math`、`cross_subject=False` → 返回 `lancedb_physics_secret / PHYSICS_SECRET / neighbor_expansion`。

转换层又不保留 `subject` 元数据：[lancedb_client.py:3449](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/agentic_rag/clients/lancedb_client.py:3449)，下游无法补滤。这直接推翻验收单“不混入别的学科笔记”的声明。

验证限制：未跑全量 CI、真实 LangGraph/LLM 或 `test_agents_dedup.py`；未访问真实 Vault/Neo4j。已跑隔离 HEAD 定向套件、真实 tmp LanceDB 反例及 7 个变异。

总结论：REJECT


