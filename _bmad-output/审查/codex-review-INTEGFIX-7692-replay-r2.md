## 审查范围与只读核验

- HEAD = `d0e42bc47c36b0aebb6d4c5cf6a76a3c3effb7be`，父提交 = `2bdbc68557a368811f7024797cf888903c32b4aa`； ancestry 已核验。
- `d0e42bc4` 只改 `backend/tests/integration/test_cypher_contract_gate.py`，语义增量为 LOW-1/2 补断言。
- 未改动文件、未连接 Neo4j、未访问网络、未运行 pytest/ruff；结论来自静态读源码和只读 git diff/show/grep。

### 直接判定

1. **Episode 断言能挡住“当前二次写 API 被提前调用”的坏实现**：  
   `record_score_history_by_record_id()` 的完整 Cypher 会创建带输入 `record_id` 的 Episode；因此 `MATCH (e:Episode) WHERE e.record_id = $rid` 从 0 变 1 会被 `:631-635` 拦下，且不受 group_id 影响。
2. **但它不能证明“整条零写”**：它只证明「无同名 Concept」和「无该精确 `record_id` 的 Episode」。若回归改走既有 `record_score_history()`，Episode 是 `randomUUID()` 且没有 `record_id`，同时还会写 Node/Canvas/CONTAINS_NODE/SCORED，这些都不会被当前两条零写断言拦住。
3. **LOW-2 的三条 Concept 计数是有效回归锁**：  
   `per_group == {A:1,B:1}` 加 `distinct == 2` 共同排除 A/B 内多余节点、null/wrong-group 同名节点、以及任何第三个同名 Concept。setup/teardown 的 `Concept.name STARTS WITH 'g21gate'` 也覆盖主 concept 与 unscoped concept。
4. **断言顺序会在前序失败时跳过后续断言**，但不会造成假绿：pytest 停在第一个失败/异常，测试已经红。若要求异常路径下的写侧证据，应在调用外包 `try/finally` 并在 fixture 清理前查询；这是取证强度问题，本 Round 不单独计缺陷。

# BLOCKER

无。

# HIGH

无。

# MEDIUM

无。

# LOW

### LOW-1｜quarantined“零写”仍是非全域探针，且 Episode 探针绑定原始 `record_id`

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:620-635`
- 相关写侧：`backend/app/clients/neo4j_client.py:1806-1820`、`backend/app/clients/neo4j_client.py:1897-1905`
- 复现思路：把 `_resolve_entry_source()` 失败分支改成先调用旧 API `record_score_history(...)` 再 `return False`。旧 API 会写 `Node`、`Canvas`、`CONTAINS_NODE`、随机 `id` 的 `Episode`、`SCORED`，但不写 Concept，也不给 Episode 写传入的 `unscoped_rid`。
- **未被拦下的输入**：  
  `record_score_history()` / raw Cypher 写出 `Node + Canvas + CONTAINS_NODE + Episode{id:randomUUID()} + SCORED`；或 Episode 的 `record_id` 被改写为 hash/random/None；或只 MERGE `User {id:'default_user'}`。
- **对照输入**：当前实现 `_resolve_entry_source()` 返回 None 后在 `fallback_sync_service.py:912-920` 直接拒写，两个探针均为 0。
- **负控输入**：同一提前写分支改调 `record_score_history_by_record_id(record_id=unscoped_rid, ...)`；Episode 探针变为 1，当前新断言红灯，说明 LOW-1 原目标已锁住。
- **盲区**：无 User/Node/Canvas/CONTAINS_NODE/SCORED 零写或门前缀总量 delta 断言；注释中“整条零写”的表述强于实际证明面。

### LOW-2｜新 Episode 探针使用固定 `unscoped_rid`，但 setup/teardown 不直接清理该 record_id

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:96-110`、`backend/tests/integration/test_cypher_contract_gate.py:613-635`
- 复现思路：先由某个坏实现留下孤儿节点 `(:Episode {record_id:'g21gate_replay_unscoped_rid', type:'scoring', group_id:'vault__default__g21gate_replay'})`，无任何 relationship、group_id 非 null 且不以 `vault__g21gate` 开头；随后恢复到当前 HEAD 重跑。
- **未被拦下的输入**：这不是假绿输入，而是**假红/粘滞残留输入**——当前实现拒写成功、Concept=0，但 Episode 精确计数仍为 1，测试继续红。
- **对照输入**：带该 rid 的 Episode 若挂在 `g21gate_*` Node 下，`:108` 会删；若 `group_id IS NULL` 且孤儿，`:109` 会删；若 group 是 `vault__g21gate*`，`:97` 会删。
- **负控输入**：cleanup 增加按 `e.record_id STARTS WITH 'g21gate_'` 删除的负控会消除该残留路径；当前提交没有该清理面。
- **盲区**：Concept 名称清理充分（`:98` 覆盖 `g21gate_replay_concept` 与 `g21gate_replay_unscoped_concept`），但 Episode 只能经 group/Node/孤儿-null 间接清理，不能直接按新引入的固定 rid 清理。

### LOW-3｜四文件门收编后仍未锁死完整来源优先级矩阵，特别是 `group_id` vs `vault_id` 冲突与 env 正向分支

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:545-563`；`backend/tests/integration/test_replay_rewrite_7692.py:217`、`:426-444`、`:452-468`
- 对照实现：`backend/app/services/fallback_sync_service.py:627-637`
- 复现思路：把 `_resolve_entry_source()` 的顺序改成 `vault_id` 优先、`group_id` 其次。四文件门中，cypher gate 的 scoring 条目只有 `group_id`，7692 gate 的条目只有 `vault_id`，没有任何一条同时携带两者，因此重排后仍可全绿。
- **未被拦下的输入**：  
  `{group_id: vault:A..., vault_id: B}` 应落 A，但重排实现落 B；以及删除 `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 正向 fallback 的实现——集成 gate fixture 在 `test_replay_rewrite_7692.py:217` 明确删除该 env，只测无 env 时 quarantine。
- **对照输入**：当前实现先返回非空 `entry_group`，再处理 `vault_id`，最后 env。
- **负控输入**：一条集成用例同时给冲突 `group_id=A` / `vault_id=B` 并断言物理组为 A；另一条只有 env vault、无 entry group/vault，并断言按 env 构组。当前四文件门没有这两条。
- **盲区**：`test_replay_rewrite_identity.py:333-339` 有 env 单测但不在声称的四文件集成门内；即使把它加入，也仍缺 group/vault 冲突判据。该问题是 r1 LOW-3 的门选择残余，不是 `d0e42bc4` diff 本身引入。

清零：否（仍有 LOW×3）；B/H/M/L = 0/0/0/3
