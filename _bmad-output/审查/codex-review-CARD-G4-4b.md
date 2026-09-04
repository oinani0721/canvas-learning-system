结论：核心修复有效，未发现阻断级问题；但有 3 条声明过宽的 HIGH，以及 1 条非阻断的 `cross_subject` 召回问题。

## Findings

1. **HIGH — “缺 `subject` 列没有新增 schema 风险”的论证不成立。**

   `course_id` 分支主检索的是 `vault_notes`：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:381)，邻居却固定查询 `canvas_nodes`：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:430)。因此并非所有路径都满足“同一张表的主检索早已依赖 subject”。

   临时真 LanceDB 反例：缺 `subject` 列的 `canvas_nodes` 在 `subject=None` 时返回 `seed + neighbor`，在 `subject="math"` 时只返回 `seed`；异常被 [lancedb_client.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:2363) 静默吞掉。搜索 schema guard 也确实未处理 `subject`：[lancedb_client.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:3312)。

   验收单的“主检索早就坏了／没有新增依赖面”结论过宽：[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4b-邻居扩展subject过滤-2026-09-04.md:203)。这是召回损失，不是持久数据丢失或安全泄漏，故非阻断。

2. **HIGH — M2 本身不能排除“转义后语法错误被吞空”。**

   M2 的确证明去掉转义后条件合法且恒真，并真实带回两行：[mutation-run.txt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/审查/evidence-g44b/mutation-run.txt:7)。但它不能证明保留转义时查询没有抛异常；正向测试只断言两行不存在：[test_agentic_rag_vault_scope.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/unit/test_agentic_rag_vault_scope.py:716)，而异常正会被静默吞掉。因此 [UAT 对 M2 的归因](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4b-邻居扩展subject过滤-2026-09-04.md:101) 比该证据本身宽。

   不过我独立直接执行 LanceDB filter 后确认当前实现安全：LanceDB 0.30.2 下，反斜杠、双反斜杠、Unicode 引号、注释符、换行、预加倍引号等载荷均无异常且零命中；未转义对照返回 math、physics 两行。所以这是证据归因问题，不是实际注入漏洞。结论严格绑定当前版本；依赖只约束 `lancedb>=0.14.0`：[requirements.txt](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/requirements.txt:76)。

3. **HIGH — 新注释及闭合措辞仍过宽。**

   新注释称 `state["subject"]` 与 VaultScope 二级同源且分裂会告警：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:427)。反例是 HTTP 允许 `subject_id=""`：[rag.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/api/v1/endpoints/rag.py:76)；VaultScope 会改走 canvas 二级：[subject_config.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/core/subject_config.py:256)，state 保留空串，而哨兵直接返回：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:80)。

   同时验收单称“边界完整／其余无变化／功能面收口”，却又登记 `cross_subject` 会收窄：[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4b-邻居扩展subject过滤-2026-09-04.md:31)、[同文件](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4b-邻居扩展subject过滤-2026-09-04.md:221)。闭合措辞应限定为“非空 subject、`cross_subject=False`”。

4. **MEDIUM — `cross_subject=True` 确实过度收窄，但登记后卡足够。**

   主检索循环搜索多值 `subjects_to_search`：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:339)，合并后邻居扩展却只传原始单值：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:430)。临时库实测：physics 主结果保留，但其 physics wiki 邻居被 `subject="math"` 丢弃，甚至可能改带同名 math 邻居。

   这不是安全边界扩大，只是召回质量下降。实际卡文 §三(b)/(d) 明定单值 subject 和透传 `state["subject"]`，没有 `cross_subject` 完成条件，因此 R2 登记足够，不要求本卡改代码；但上述无条件闭合文案必须收窄。

## PASS 项

- **PASS — 向后兼容。** 新参数追加在签名末尾：[lancedb_client.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:2277)；`None` 跳过新增分支，基础 where 与基线逐字相同：[lancedb_client.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:2344)。仓内只有一个生产调用点，没有位置参数迁移。

- **PASS — 空串未引入新的链内分叉。** 主检索早已把空串视为未指定：[nodes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:341)，邻居过滤同样跳过。它是可达输入，但不代表一个可过滤的有效 subject。

- **PASS — D1 丢弃语义成立。** `subject="math"` 只返回 math 邻居，physics 被排除；`subject=None` 正向对照仍返回两科。

- **PASS — 变异门。** 我在隔离的临时 HEAD 副本中重放 M1/M2/M3，3/3 均以指定断言 `exit=1` 被杀；实际工作树两份生产文件 SHA 前后相同，零 `MUTANT` 残留。

- **PASS — 指定裁判。** `23 passed / 0 xfailed`；另一文件 `12 passed + 3` 条已裁决基线红；4a 三个端点文件 `69 passed`；ruff 通过。未连接 live vault 或 Neo4j。

六个未证明项中，只有 #2 的“缺列不构成新增风险”必须在本卡内撤回、限缩或补证；#3 只需收窄注释；#4 的代码可按卡文登记后卡，但顶层闭合声明现在就应限缩；其余无需扩大本卡证明面。

阻断级 = 0


