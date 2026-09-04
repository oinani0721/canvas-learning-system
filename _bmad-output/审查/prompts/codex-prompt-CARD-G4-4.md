# CARD-G4-4 定向对抗审查请求（full RAG 显式 VaultScope）

你是对抗性代码审查员。审查对象：worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope`（分支 card/w8-scope）上 BATCH-2026-09-01-第八批 / CARD-G4-4 的实现。

## 卡文（唯一真相源，逐条核对）

`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W8-2.md`

## 本卡改动范围（commit ca116f51 → HEAD）

- `backend/app/api/v1/endpoints/rag.py` — RAGQueryRequest.vault_id 必填；handler 改走 resolve_vault_scope（chat.py:284-296 范式）；删「缺省不注入」旁路；新增日志惰性参数 + notry 包装。
- `backend/lib/agentic_rag/nodes.py` — compress_context 的 memory_group_id 改读 app.core.vault_scope.current_vault_id()；三节点（retrieve_graphiti / retrieve_lancedb / compress_context）加 _warn_subject_scope_mismatch 哨兵。
- `backend/app/api/v1/endpoints/agents.py` — 8 个 resolve 调用点改 resolve_vault_scope，经 X-Vault-Scope-Source 响应头加性透出 VaultScope.source；12 个 handler 签名注入 response: Response；vault_id 保持 Optional（裁决②）。
- 新测试 `backend/tests/api/v1/endpoints/test_rag_vault_scope_api.py`（15 用例）+ `backend/tests/unit/test_agentic_rag_vault_scope.py`（14 用例，含 tmp LanceDB 双 vault 真库隔离）。
- 最小适配（不在独占面，理由见 commit a3c41075）：`test_rag_four_state_api.py`（autouse 钉 active vault + POST 带 vault_id）、`test_agents_learning_event.py`（handler 调用注入 response=）。

## 重点审查项（卡文点名）

1. **默认组旁路残留**：是否仍有绕过 VaultScope 的默认组路径？rag 链（端点→rag_service→nodes）还有没有「缺参落默认组/不注入」的分支？grep 门（DEFAULT_GROUP_ID|get_current_vault_id 三文件 0 命中）之外有没有语义等价的残留？
2. **422/409 与 G2-2 裁定一致性**：resolve_vault_scope 的 409 别名集语义（active_vault_aliases 三候选）在 rag.py 是否被正确继承，有没有二次解析/绕过唯一解析点？
3. **双 vault 测试是否真隔离**（非同组 fixture 假绿）：`test_agentic_rag_vault_scope.py::TestDualVaultIsolationOnTmpLanceDB` — 同一 tmp 库两表、b_unique「只有它在 B」、正向对照 + 反向对称 + 同名不同内容笔记。特别注意 DEFAULT_TABLES=["canvas_nodes"]（表名必须是 *_canvas_nodes 才会被 search_multiple_tables 默认链查到）。
4. **agents「双缺失推导 active vault」偏离是否如实声明**：裁决② 与总账 G4-4 档案「缺参 fail-closed」的显式偏离，验收单是否显著声明。
5. **卡文与实现的三处已声明偏差是否成立**（验收单「与卡文偏差」段）：
   a. scope_source 透出形态 = 响应头而非响应体字段（schemas.py 不在独占面 + openapi 契约面风险）；卡文三值名（explicit/legacy_group_id/derived_active）与 VaultScope.source 实际值域（request-vault/legacy-group/active-vault）的映射声明。
   b. 卡文预写「vault:default 污染桶抛 VaultScopeUnresolved 属预期」与代码不符 — current_vault_id() 无形状校验不抛，测试按真实行为锁定（test_pollution_bucket_returns_default_segment_without_raising）。
   c. test_rag_four_state_api.py / test_agents_learning_event.py 的跨独占面最小适配。
6. **并发车道声明**：同 worktree 有 OBS-nothrow-logging 车道 session 并行（nothrow_logging 系列未提交文件 + memory.py 改动属它）；本卡裁判 2 的 comm 比对排除了其引入的 test_nothrow_logging_api.py（基线不存在该文件，其 3 条失败不是本卡回归）。

## 证据锚点（可直接复核）

- 裁判 1（四文件 71 passed + 3 存量红）：3 红为 test_lancedb_vault_isolation.py 开工即红的 yaml 环境耦合基线（Settings.vault_id 优先读 .canvas-config.yaml 的 canvas_vault，压过 reload_settings override；同文件 :150-157 注释记录过同类坑）。
- 裁判 2：`cd backend && .venv/bin/pytest tests/api -q -p no:cacheprovider -k 'rag or agents' --deselect tests/api/v1/endpoints/test_agents_dedup.py -rA` → 92 passed，与开工基线（77 passed 全绿）comm 零新增失败（排除 nothrow 文件后）。
- 变异：5 个（去422/去409/内链改回进程级/fixture同组化/哨兵降debug）各杀指定门，还原逐字节一致。

## 输出要求

逐条给 verdict：BLOCKER / HIGH / MEDIUM / LOW / PASS，每条附 file:line 证据。不要复述代码。发现「声明比证据宽」（验收单/注释声称了它没证明的东西）按 HIGH 起。最后给一行总结论：ACCEPT / ACCEPT-WITH-NOTES / REJECT。

---

# ROUND-2 复审请求（round-1 REJECT 整改对照）

本轮请**只复核**以下 round-1 各项的整改是否成立（逐条给 PASS/FAIL + 证据），并对新改动做常规对抗扫描：

| round-1 项 | 整改声称 | 复核锚点 |
|---|---|---|
| BLOCKER-1 expand_neighbors 裸表旁路 | nodes.py 改传 `client.resolve_table_name("canvas_nodes")` 与主链同源同表；新门 test_wikilink_neighbor_expansion_stays_in_vault（裸表 b_secret 泄漏探针 + a_neighbor 活性对照）；M6 变异杀门。⚠️ 注意整改中修正过一次：第一版 resolve("vault_notes") 仍会 B0.7 回退裸表（vault_a_vault_notes 不存在），故统一到 canvas_nodes 系——请复核现值 | nodes.py expand 调用；unit 文件新用例；B0.7 回退剩余面已登记移交（验收单 §未证明 #4） |
| BLOCKER-3 fixture 不能证明 full RAG 隔离 | fixture 增加裸 legacy 表 vault_notes（只放 B secret）；泄漏探针 + 活性对照双断言；「提升为全链结论」的措辞已从验收单撤回（改为分段链证明 + §未证明 #2/#4 声明） | unit fixture + 验收单 4-A #8 / §未证明 |
| HIGH-2 空白 vault_id 绕 422 | RAGQueryRequest.field_validator fail-closed；3 空白形态（含全角空格）参数化 422 + 服务零调用断言；M7 杀门 | rag.py validator；API 文件参数化用例 |
| HIGH-4 test_recommend_action.py 10 回归 | 10 处直调注入 response=Response()；1 处 mock 裸 Exception 改 RuntimeError（handler 只优雅降级预期依赖故障是设计行为，注释说明）；该文件现在全绿 | 该文件 diff + 全绿运行 |
| HIGH-4 附带「理由不实/数字不准/覆盖面过宽」 | 验收单 v2 重写：裁决②理由更正（main.ts:360-366 反证已如实呈现，是否收紧升裁决点⑥）；7 调用点；「12 个带作用域解析的 POST handler」；新增 §6.5 与卡文偏差逐对映射表（含响应头不进 openapi 声明） | 验收单 v2 §先读2 / §6-② / §6.5 |
| HIGH-5 偏差披露不完整 | 验收单新增 §6.5 偏差表 a-f | 验收单 §6.5 |
| HIGH-6 交付完整性 | test_rag_vault_scope_api.py 已 tracked（aaecf696）；验收单 + codex 存档随本轮 commit 入库；d6a5e697 归属更正为 DEBT-8；OBS 时序更正（78c9e6e7 已先于本卡整改落地，两车道 rag.py 改动共存且本卡裁判在其上全绿） | git log + 验收单 §未证明 #9 |
| HIGH-7 变异证据缺陷 | 脚本 v2：exit==1 才算杀（usage error 硬失败）；M5 改真降级 warning→debug；新增 M6/M7；v1 M5 exit=4 根因更正为脚本 gate 路由 bug（前归因「并发抖动」有误，已在验收单 §6 error 区更正）。7/7 杀门归档 | evidence-g44/mutation-run.txt (v2) |

新改动面（round-1 整改引入，常规扫描）：rag.py field_validator / nodes.py expand 表源 / test_recommend_action.py 适配 / 两个测试文件的新用例。

输出格式同前。审查锚点：当前 HEAD。
