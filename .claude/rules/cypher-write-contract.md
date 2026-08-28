# Cypher 写契约（W1-W5）

> **来源**: BATCH-2026-08-27-第四批 / CARD-G2-1 Cypher 读写契约审计
> **审计清单**: `_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`
> **真库门测试**: `backend/tests/integration/test_cypher_contract_gate.py`（7692 测试容器；G2-3 已去 xfail 翻绿 + 门 4 扩展行为门）
> **执行级别**: docstring 约定 + `lefthook.yml::cypher-vault-filter-lint` + 真库门测试。
> **G2-3 修复记录（BATCH-2026-08-28-第五批）**: 本文档下列 W1×5 / W2×2 / W5×1 存量违规已全部修复——group 进 MERGE/MATCH 锚定键，`neo4j_client._resolve_physical_group_id()` 先解析后进键，解析失败 fail-closed 拒写（logger.error 首日观察，不静默降级 DEFAULT）。存量数据迁移器：`backend/scripts/migrate_write_identity_g23.py`（现网 7691 dry-run 实测 pending=0，证据 `_bmad-output/审查/evidence-g23/`）。

## ⚠️ 与根 CLAUDE.md 的矛盾记录（如实，不代改）

根 CLAUDE.md 的"必须用 `cypher_with_group_filter()`"条款对**写侧完全失效**：该 helper 对 MERGE/CREATE 开头的写查询注入产生**非法 Cypher**（`WHERE ... MERGE ...`，2026-08-27 真库 EXPLAIN 实测 `Neo.ClientError.Statement.SyntaxError`），生产调用 = 0。写侧防御从来只能靠查询本身的身份键设计，helper 帮不上忙。修订根 CLAUDE.md 本体 = 移交事项，不在本卡范围。详见 `cypher-read-contract.md` 同名章节。

## 规则

### W1 — write identity：业务节点 MERGE/CREATE 身份键必须含 group_id 复合键

MERGE 业务节点时，group_id 必须在**身份键（merge key）里**，而不是 MERGE 后 SET：

```cypher
-- ✅ 合规
MERGE (c:Concept {name: $name, group_id: $group_id})
-- ❌ 违规：跨 vault 同名节点合并成一个，后写 vault 的 SET 覆盖先写 vault 的归属
MERGE (c:Concept {name: $name})
SET c.group_id = $group_id
```

**存量违规（写身份缺 group 复合键，5 处，`backend/app/clients/neo4j_client.py`）——✅ 已全部由 G2-3 修复（2026-08-28）**：
1. `create_learning_relationship`——现为 `MERGE (c:Concept {name, group_id})` + `MERGE (u)-[r:LEARNED {group_id}]->(c)` 复合键；
2. `create_canvas_node_relationship`——现为 `MERGE (c:Canvas {path, group_id})` / `MERGE (n:Node {id, group_id})` / `CONTAINS_NODE {group_id}`；
3. `create_edge_relationship`——Canvas/Node/CONNECTS_TO 三层全复合键化（`CONNECTS_TO {edge_id, group_id}`）；
4. `record_score_history`——Node/Canvas 复合键 + Episode/SCORED 携带 group_id；
5. `create_canvas_association`——Canvas ×2 复合键 + `ASSOCIATED_WITH {association_id, group_id}`。

统一模式：`_resolve_physical_group_id(group_id, canvas_path)` 先解析（显式 → ContextVar → canvas_path 推导）后进键，恒物理化恒非 null；解析失败 → `logger.error` + 返回 False（fail-closed，防 null 进 MERGE 键的服务端 500，也防静默降级 DEFAULT 跨 vault 污染）。`test_cypher_contract_gate.py` 两条 xfail 已去标翻绿，门 4 新增 6 条扩展行为门。

### W2 — scoped delete：DELETE 默认必须带 group scope

`DELETE` / `DETACH DELETE` 的 MATCH **默认必须含 group_id 过滤**。唯一窄例外（Codex round-1 HIGH 整改，与 R3 口径统一）：按**可证服务端 uuid4 级生成**的 ID 点删（生成点可在代码中追溯），且即便如此仍推荐叠加 group scope 作防御深度。来源不可证的 ID（外部传入 / 端点拼接 / 截断派生）不享受此例外。

**存量违规（无 scope 删除，2 处，`neo4j_client.py`）——✅ 已全部由 G2-3 修复（2026-08-28）**：
1. `delete_edge_relationship`——现为 `MATCH ()-[r:CONNECTS_TO {edge_id, group_id}]->()`，group 解析失败 fail-closed 拒删（`canvas_service.delete_edge` 链路已下传 canvas_path 供解析）；
2. `delete_canvas_association`——现为 `ASSOCIATED_WITH {association_id, group_id}` 复合匹配删除，同 fail-closed。

### W3 — physical write：写入 group_id 属性前必须物理化

写入任何 group_id 属性前必须 `to_physical_group_id()`（`vault__x`）。正例：`create_learning_relationship` L738、`sync_service` 写侧。禁止把 D16 冒号格式（`vault:x`）直接落库——graphiti_core validator 拒收，且与读侧过滤条件错格。

### W4 — declared cross-vault write：跨 vault 写必须显式声明

迁移/管理工具的跨 vault 写（如 `group_id_migration_service.py` 的 UPDATE group_id）必须显式声明，并优先支持 dry-run。业务路径出现无声明跨 vault 写 = 事故级违规。

**声明形态口径（与 R2 统一）**：明确的 docstring/注释声明 = 合规最低线；`@allow_cross_vault(reason=...)` 装饰器 = 推荐标准形态（advisory backlog 补挂，非违规）。

### W5 — scoped update：MATCH...SET 的匹配 scope 遵循 W1/W2 同等要求

更新（`MATCH ... SET`）的匹配子句同样默认必须 group scope；uuid 点更的窄例外与 W2 完全同口径（服务端 uuid4 生成可证）。

**存量违规（1 处，`neo4j_client.py` #16）——✅ 已由 G2-3 修复（2026-08-28）**：`update_canvas_association` 现为 `ASSOCIATED_WITH {association_id, group_id}` 复合匹配更新，解析失败 fail-closed 拒更。

## 交接链（Codex round-1 修订 → G2-3 收口 2026-08-28）

- **G2-3 ✅ 完成**：W1 五处写身份（#1/#5/#6/#9/#10）+ W2 两处无 scope 删除（#7/#15）+ W5 一处无 scope 更新（#16）全部修复；`fallback_sync_service.py`（原 :352/:458）同形同修 + `_build_group_id_from_canvas` 返 None 分支 fail-closed；JSON 镜像层 `_handle_merge_learning` 同型双键修复。
- **门测试**：两条 xfail 去标翻绿 + 门 4 扩展（Canvas/Node 双组独立、score history 双组独立、删 A 不影响 B、update A 不动 B、fallback replay 不合并、group 缺失 fail-closed 防 500）+ 迁移器行为门 `test_migrate_write_identity_g23.py`（dry-run 零写入 / apply 分裂正确 / 7691 硬拒）。
- **遗留边界（如实声明）**：Canvas/Node/Episode 层的**读侧**无 group 查询（审计 §5 #8/#11-14/#17/#18）仍属读侧收敛卡范围，G2-3 只修写侧；写侧复合键化后新旧节点在过渡期可能并存（现网实测无此存量，`legacy_informational` 全 0），跨层收敛由 G2-9 隔离 canary 收口。
- 存量逐条分类、violation 全清单：见审计文档 `_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`（§9 为 Codex round-1 整改记录）。
