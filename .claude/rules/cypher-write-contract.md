# Cypher 写契约（W1-W5）

> **来源**: BATCH-2026-08-27-第四批 / CARD-G2-1 Cypher 读写契约审计
> **审计清单**: `_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`
> **真库门测试**: `backend/tests/integration/test_cypher_contract_gate.py`（7692 测试容器；写身份现状 = `xfail(strict)`，交接 G2-3 翻绿）
> **执行级别**: docstring 约定 + `lefthook.yml::cypher-vault-filter-lint` + 真库门测试。
> **无运行时强制**——本卡铁律：不改任何业务写路径与 helper 行为，fail-fast 降级为文档+lint 提示。

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

**存量违规（写身份缺 group 复合键，5 处，`backend/app/clients/neo4j_client.py`）**：
1. `create_learning_relationship`（L725-736）——`MERGE (c:Concept {name})` + 后置 `SET c.group_id`，跨 vault 同名概念互相clobber（真库门测试已固化为 xfail(strict)）；
2. `create_canvas_node_relationship`（L1071-1079）——`MERGE (c:Canvas {path})` / `MERGE (n:Node {id})`，无 group_id；
3. `create_edge_relationship`（L1114-1122)——Canvas/Node/CONNECTS_TO 全无 group_id；
4. `record_score_history`（L1286-1300）——`MERGE (n:Node {id})` / `MERGE (c:Canvas {path})` + CREATE Episode，无 group_id；
5. `create_canvas_association`（L1376-1388）——`MERGE (:Canvas {path})` ×2 + ASSOCIATED_WITH，无 group_id。

修复 = G2-3 范围（本卡铁律不改写路径）。修复后 `test_cypher_contract_gate.py` 的两条 xfail(strict) 会 XPASS 报错，届时移除 xfail 标记翻绿。

### W2 — scoped delete：DELETE 默认必须带 group scope

`DELETE` / `DETACH DELETE` 的 MATCH **默认必须含 group_id 过滤**。唯一窄例外（Codex round-1 HIGH 整改，与 R3 口径统一）：按**可证服务端 uuid4 级生成**的 ID 点删（生成点可在代码中追溯），且即便如此仍推荐叠加 group scope 作防御深度。来源不可证的 ID（外部传入 / 端点拼接 / 截断派生）不享受此例外。

**存量违规（无 scope 删除，2 处，`neo4j_client.py`，新口径下判定自洽）**：
1. `delete_edge_relationship`（L1146-1150）——按 `edge_id` 属性全库删 CONNECTS_TO（edge_id 可退化为端点拼接值，见 `neo4j_edge_client.py:165-168`，唯一性不可证）；
2. `delete_canvas_association`（L1638-1642）——按 `association_id` 删：该 ID 由调用方外部传入、无服务端生成点约束，uuid4 来源**不可证**，不满足窄例外；MATCH 又无 group 限定 → 违规。

### W3 — physical write：写入 group_id 属性前必须物理化

写入任何 group_id 属性前必须 `to_physical_group_id()`（`vault__x`）。正例：`create_learning_relationship` L738、`sync_service` 写侧。禁止把 D16 冒号格式（`vault:x`）直接落库——graphiti_core validator 拒收，且与读侧过滤条件错格。

### W4 — declared cross-vault write：跨 vault 写必须显式声明

迁移/管理工具的跨 vault 写（如 `group_id_migration_service.py` 的 UPDATE group_id）必须显式声明，并优先支持 dry-run。业务路径出现无声明跨 vault 写 = 事故级违规。

**声明形态口径（与 R2 统一）**：明确的 docstring/注释声明 = 合规最低线；`@allow_cross_vault(reason=...)` 装饰器 = 推荐标准形态（advisory backlog 补挂，非违规）。

### W5 — scoped update：MATCH...SET 的匹配 scope 遵循 W1/W2 同等要求

更新（`MATCH ... SET`）的匹配子句同样默认必须 group scope；uuid 点更的窄例外与 W2 完全同口径（服务端 uuid4 生成可证）。

**存量违规（1 处，`neo4j_client.py` #16）**：`update_canvas_association`（L1743-1747）仅按外部传入的 `association_id` 匹配（来源不可证），无 group 限定 → W5 违规。

## 交接链（Codex round-1 修订）

- **G2-3**：修复 W1 五处写身份（#1/#5/#6/#9/#10）+ W2 两处无 scope 删除（#7/#15）+ **W5 一处无 scope 更新（#16，round-1 曾漏列）**；`fallback_sync_service.py:352/458` 同形同修。
- ⚠️ **门测试覆盖诚实声明**：现有两条 xfail(strict) **只覆盖 #1**（Concept/LEARNED 写身份）。G2-3 翻绿这两条 ≠ 全量验收——修其余 7 处时应按同模式为每类违规扩展至少一条真库行为门。
- 存量逐条分类、violation 全清单：见审计文档 `_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`（§9 为 Codex round-1 整改记录）。
