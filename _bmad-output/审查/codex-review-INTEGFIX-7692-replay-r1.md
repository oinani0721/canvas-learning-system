## 审计锚点与只读验证

- 工作树：`batch15/integ`，HEAD = `2bdbc68557a368811f7024797cf888903c32b4aa`，父提交 = `69d26ed5f4d6ed752675409bb89eba24325fd61d`。
- `git diff --name-status 69d26ed5 2bdbc685`：只改 `backend/tests/integration/test_cypher_contract_gate.py`，+152/-205。
- 当前工作树另有两个未跟踪审查/evidence 路径；它们不属于被审 commit，本次未读取内容、未修改。
- 我未连接 Neo4j、未访问网络、未跑 pytest。只做了 git/文件读取、AST 只读比较，以及本地 `ruff check --no-cache` / `ruff format --check --no-cache`：均通过。
- AST 对照：删除目标测试后，父提交与修复提交整个模块 AST 完全相同；函数级对照也只有 `test_fallback_replay_write_identity_dual_vault` 及其嵌套 `_replay` 变化。因此 ruff 重排未藏入其它函数/模块级语义变化。

### 逐问裁定

1. **原不变量强度：PASS，等价。**  
   当前 `backend/tests/integration/test_cypher_contract_gate.py:544-585` 仍保持原写序：scoring A → learning B → scoring B 第二笔 → learning A 第二笔；最终回查仍精确要求 `(A,A,81)`、`(B,B,61)`。父提交同断言在 `69d26ed5:backend/tests/integration/test_cypher_contract_gate.py:555-566`。查询不按组过滤，只按概念名取全部 LEARNED 边并按 `cgid` 排序，因此错组、额外边、重复边、分数错都会红。组内后写覆盖仍由 01:00 条目覆盖 00:00 条目验证。
2. **active-vault 负控：PASS，可判别，不恒绿。**  
   若实现回退为“active vault 优先”，四笔结果会变成：scoring A 落 B(80) → learning B 覆盖 B(60) → scoring B 落 A(61) → learning A 覆盖 A(81)，最终是 `(A,81),(B,60)`，与期望 `(A,81),(B,61)` 在 B 组分数上必红。若写侧回执守卫先行发现组错，则 `all(ok)` 更早红。MERGE 键中的 group_id 不会掩盖：该值正是被测解析结果传下去的 `physical_group`。
3. **quarantined 断言：主路径 PASS，覆盖面有 LOW 盲区。**  
   `monkeypatch.delenv` 在调用点实时移除 `CLS_REPLAY_LEGACY_NOSCOPE_VAULT`；entry 无 `group_id`/`vault_id`，但 concept、canvas、timestamp、score 都有效。当前 `_resolve_entry_source` 在 `backend/app/services/fallback_sync_service.py:627-635` 返回 `(None,"quarantined")`，调用方在 `:912-920` 先返 False，之后才进入 record_id/Episode/写图路径。概念名独立且断言位于前段身份回查之后，不污染前段断言。
4. **不是掩盖产品回归；有充分证据是本批有意契约。**  
   卡文 `_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P2-C.md:4` 明确要求“来源 vault 落盘”，`:27` 要求条目 vault 战胜 active、无来源默认隔离；UAT `_bmad-output/验收单/UAT-CARD-REPLAY-REWRITE-2026-09-20.md:11-14` 写明新条目带 `record_id/vault_id/group_id/schema_version=2`，`:133` 明确历史迁移归 G4-6。实现侧 `fallback_sync_service.py:619-646` 与 `:869-889` 也明写不看 active vault。生产写者已补身份戳：`failed_writes_constants.py:478-546`、`memory_service.py:513-523`、`agent_service.py:132-148`、`memory_service.py:2933-2943`。learning 链仍保留 active-vault 路径（`fallback_sync_service.py:1137-1194`），与测试注释一致，不是本卡改面。既有真库门 `test_replay_rewrite_7692.py:426-468` 也分别覆盖“entry vault 战胜 active”和“历史无来源 quarantined”。
5. **ruff 重排语义等价：PASS。**  
   除目标测试函数和嵌套 helper 外，父/子提交 AST 完全一致；模块去掉目标测试后 AST 也完全一致。当前文件 ruff check/format check 均绿。

---

## BLOCKER

无。

## HIGH

无。

## MEDIUM

无。

## LOW

1. **`backend/tests/integration/test_cypher_contract_gate.py:587-602` — “零写图”只验证 Concept，未验证全部写面。**  
   复现思路：未来把 Episode/Node 写侧提前，或在 LEARNED 失败后仍执行 `record_score_history_by_record_id`，该测试可能只看 `Concept count==0` 而漏掉 Episode。  
   - 未被拦下的输入：无来源 entry 携带唯一 `record_id`，错误实现只写 Episode/Node/User 而未写 Concept。  
   - 对照输入：当前实现在 `fallback_sync_service.py:912-920` 于任何写侧前返 False。  
   - 负控输入：只要错误实现写出同名 Concept，无组过滤的 count 会红。  
   - 门未覆盖的路径：未按 `record_id` 断言 Episode=0，也未断言 Node/User/总写入数或拒绝日志 reason。

2. **`backend/tests/integration/test_cypher_contract_gate.py:574-585` — “每组恰一节点”只能由边行间接证明，孤儿 Concept 不可见。**  
   复现思路：额外创建同名同组但无 LEARNED 边的 Concept，当前回查仍可绿。  
   - 未被拦下的输入：额外孤儿 `Concept {name, group_id}`。  
   - 对照输入：额外 LEARNED 边、错组边、重复边会让精确 row-list 红。  
   - 负控输入：单键 MERGE/SET 串写会改变 A/B 分数或组身份，会被抓住。  
   - 门未覆盖的路径：没有独立 `count(DISTINCT c)==2` / 每组 `count(c)==1`；另外 00:00 同刻 LWW tie 会被后续 01:00 写入掩盖。该盲区父提交同样存在，非本 commit 引入。

3. **`backend/tests/integration/test_cypher_contract_gate.py:544-570` — 本文件只打中 `entry group_id` 短路分支，未锁 `entry vault_id` / env 优先级。**  
   复现思路：仅改变 `_resolve_entry_source` 的 `group_id > vault_id` 优先级，或破坏 vault-only 条目解析，本文件目标测试仍可能绿。  
   - 未被拦下的输入：同时带冲突 `group_id` 与 `vault_id` 的条目；仅带 `vault_id` 的条目；env legacy-vault 条目。  
   - 对照输入：`test_replay_rewrite_7692.py:426-444` 已用 entry vault + 不同 active 验证 vault-only 来源，`:452-468` 验证无来源隔离。  
   - 负控输入：本文件 `:587-602` 只验证 env 缺失且完全无来源的拒写。  
   - 门未覆盖的路径：用户指定的两文件 7692 门选择不包含 `test_replay_rewrite_7692.py`，因此该优先级矩阵在这两文件门内不完整。

清零：是（BLOCKER/HIGH=0；LOW 为覆盖盲区登记，非当前实现回归）  B/H/M/L = 0/0/0/3


