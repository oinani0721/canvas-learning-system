# Cypher 读契约（R1-R5）

> **来源**: BATCH-2026-08-27-第四批 / CARD-G2-1 Cypher 读写契约审计
> **审计清单**: `_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`
> **真库门测试**: `backend/tests/integration/test_cypher_contract_gate.py`（7692 测试容器）
> **执行级别**: docstring 约定 + `lefthook.yml::cypher-vault-filter-lint`（staged diff 启发式）+ 真库门测试 + **R1/R4 的运行时 fail-closed helper**（G4-1a 起，见下）。
> **G4-1a 更新（BATCH-2026-08-29-第六批，2026-08-30）**: 原"无运行时强制"是 G2-1 本卡铁律下的临时状态。G4-1a 落地 `backend/app/core/vault_scope.py` 的读侧 API（`require_read_group()` / `read_scope_params()` / `read_group_filter()` / `group_in_read_scope()`），R1/R4 在**已封堵的调用点**上有了运行时 fail-closed；未封堵的存量站点仍只受文档+lint 约束。

## ⚠️ 与根 CLAUDE.md 的矛盾记录（如实，不代改）

根 CLAUDE.md 写有：*"Cypher 查询防御: 必须用 `backend/app/utils/cypher_helpers.py::cypher_with_group_filter()`（防忘传 group_id 跨 vault 泄漏）"*。

**实况（2026-08-27 审计实证）**：该 helper 生产调用 = **0**。全部引用为：helper 自身定义/docstring、单元测试（`test_cypher_helpers.py`、`test_lancedb_isolation_assertions.py`）、lefthook lint 提示文案（`lefthook.yml:135`）、以及 `verification_service.py:2117` 的**显式拒用注释**。

helper 已知两大局限（真库实证，见审计清单 §2）：
1. **单 alias 启发式注入**——多 alias 查询（如 verification_service 需同时过滤 b/n/m 三个 alias）无法覆盖，只能手写 WHERE；
2. **MERGE/CREATE 开头的查询注入产生非法 Cypher**——`cypher_with_group_filter("MERGE (n:Concept {name:$name}) RETURN n", gid)` 输出 `WHERE ... MERGE ...`，真库 EXPLAIN 报 `Neo.ClientError.Statement.SyntaxError`（2026-08-27 于 7692 测试容器实测）。

因此本契约**不再要求"必须用 helper"**：helper 仅适用于单 alias、MATCH 开头的查询；等价的手写 group 过滤 WHERE 同样合规（R1）。修订根 CLAUDE.md 本体 = 移交事项，不在本卡范围。

## 规则

### R1 — vault-scoped read：业务数据读取必须带 group_id 过滤

任何读取业务数据（Concept / CanvasNode / CanvasBoard / CanvasEdge / LEARNED / MasteryRecord / Exam* 等）的 Cypher，**必须**对每个可能跨 vault 的节点/关系 alias 施加 group_id 等值过滤：

```cypher
MATCH (n:Concept) WHERE n.group_id = $group_id RETURN n
-- 或 map 形式
MATCH (n:Concept {group_id: $group_id, name: $name}) RETURN n
```

- 多 alias 查询：**每个 alias（含关系）逐一过滤**。全覆盖正例：`targeting_material_service.py:163`（n/e/m 三侧 group 严格等值过滤，含边 e）。节点多 alias 手写 WHERE 的形态参考：`verification_service.py:2135-2151`（b/n/m 三节点 alias + `STARTS WITH $groupVaultPrefix` 子组放行——注意其 r 边未过滤，已按本条降 CONDITIONAL，见审计 §9 round-2）。
- 实现手段不限（helper 或手写 WHERE），语义等价即合规。
- **部分 alias 过滤 = CONDITIONAL，不得判 COMPLIANT**（Codex round-1 BLOCKER 整改 2026-08-27）：只过滤锚点 alias、依赖"关系/关联端不跨组"隐含前提的查询（如 `MATCH (n)-[r]-(e) WHERE n.group_id = $g` 而 r/e 未过滤）不算达标——在写身份缺陷（W1 clobber）修复前，该前提在存量图上**不可证**（r.group_id 可与锚点不同组）。带 group_id 属性的关系（如 LEARNED）必须显式过滤。

### R2 — declared cross-vault：故意跨 vault 读必须显式声明

系统级健康指标、迁移扫描、bootstrap 列表、`RETURN 1` ping、`SHOW CONSTRAINTS` schema 巡检等**设计上跨 vault**的读，必须显式声明意图。无声明的全库读一律按 R1 违规对待。

**声明形态口径（Codex round-1 MEDIUM 整改，统一双标）**：函数 docstring / 行内注释明确说明跨 vault 依据 = **合规最低线**；`@allow_cross_vault(reason=...)`（`app/utils/cypher_helpers.py`）= **推荐标准形态**（可被静态审计工具识别）。审计清单中的 `needs-decorator` 标注 = 建议补挂装饰器的 advisory backlog，**非违规**。

### R3 — identity-scoped read：仅"可证全局唯一"的 ID 点查可免 group 过滤

按全局唯一 ID 点查时可免 group 过滤，前提收紧为（Codex round-1 HIGH 整改）：**该 ID 由服务端 uuid4 级随机生成，且来源可在代码中直接证明**（如 `randomUUID()` / `uuid.uuid4()` 生成点可追溯）。合格示例：`exam_id`、`session_id`、Episode uuid。

**不合格反例（不得引用 R3 免过滤）**：
- `edge_id` — 可退化为端点 id 拼接值（`neo4j_edge_client.py:165-168`），非随机唯一；
- Canvas node `id` — 可由外部传入，缺失时仅取 UUID 前 8 位（`canvas_service.py:792-794`），碰撞面存在；
- 按文件名/标题派生的任何 ID —— 仅 vault 内唯一。

来源无法证明的 ID 一律按 R1 处理。`association_id` 虽自称 uuid，但由调用方外部传入、无生成点约束，同样不合格。

### R4 — no silent fallback：group_id 缺失禁止静默退化为全库读

"group_id 可选，不传就不过滤"的分支（如 `neo4j_client.get_review_suggestions` 的无 group 分支）是**静默跨 vault 泄漏面**。新代码禁止此模式。

**规范写法（G4-1a 起，2026-08-30）**——读侧统一走 `app.core.vault_scope`：

```python
from app.core.vault_scope import read_group_filter, read_scope_params

params = read_scope_params(group_id, context="svc.method")   # 解析失败即抛
rows = await client.run_query(
    f"MATCH (n:Concept) WHERE {read_group_filter('n')} RETURN n", **params
)
```

- `require_read_group(group_id, *, context)` — 显式值 → `current_group_id()`（per-request ContextVar，未注入时推导 active vault）→ 仍无则抛 `VaultScopeUnresolved`。**不回落 `DEFAULT_GROUP_ID`**（`vault:default` 是与写侧异组的污染桶，召回必空手）。
- `read_scope_params()` 产出 `{group_id, group_prefix}`（已 R5 物理化）；`read_group_filter(alias)` 产出该 alias 的 WHERE 片段。多 alias 查询逐个调 filter、共用一份 params（R1 全覆盖）。
- 内存/JSON 兜底路径用 `group_in_read_scope(candidate, scope)`——与 Cypher 侧**逐字同语义**，防"Neo4j 可用/降级"两条路径给出不同可见面。
- 旧 helper `assert_group_id_required()` 仍可用于入口早 fail，但它只校验非空、不做解析与物理化，新代码优先用上面这套。

**⚠️ 前缀语义（R4 与 R1 的交汇点，不可退回等值）**：一个 vault 的数据并不全在 vault 根组——写侧按 D16 把白板级内容写进二级子组（`vault__v__board` / `vault__v__semantic` / 中文白板 punycode `vault__v__xn--…`）。2026-08-30 现网 7691 只读实测：**全库唯一的 Concept 与唯一的 LEARNED 边都落在 punycode 子组，vault 根组零命中**。所以封堵时若把过滤写成等值，泄漏堵住了但"复习建议整页空"——比泄漏更像产品坏了。规则：命中 = 与 scope 等值 **或** 以 `scope + "__"` 为前缀；`__` 定界符是锚点的一部分（裸前缀会让 `vault__a` 吃掉 `vault__ab`）。同一规则下 canvas 级作用域仍只见本板，兄弟板不可见——保召回不得靠放宽隔离换取。真库正反双向门见 `test_cypher_contract_gate.py` 门 6。

**已封堵站点（G4-1a）**：`memory_service.get_learning_history` / `get_review_suggestions_with_status` / `search_memories_with_status`（Tier 1/2/3 + legacy graphiti 路径）、`learning_context_service._fetch_tips_and_errors`、`conversation_inheritance._fetch_neighbor_records_for_inheritance`、`neo4j_client.get_concept_score_history` / `get_learning_history` / `get_review_suggestions`（有 group 分支）。

**未封堵存量**：`neo4j_client` 的 `get_concept_history` / `get_canvas_associations`（4 分支）/ `get_canvas_concepts` / `find_common_concepts` / `get_all_recent_episodes` + JSON 镜像族 → **CARD-G4-1b**。清单见审计文档 §5 与 `_bmad-output/审查/CARD-G4-1a-验收单.md`。

### R5 — physical format：绑定物理格式，输出边界还原

- `$group_id` 绑定值必须经 `app.graphiti.group_id_compat.to_physical_group_id()` 物理化（`vault__x` 双下划线；T1 契约 2026-07-10，graphiti_core validator 拒冒号）。绑定逻辑冒号格式（`vault:x`）会导致过滤条件与库内数据不匹配、**查询静默返回空**。
- 读回的 group_id 在 API 输出边界须 `desanitize_group_id_from_graphiti()` 还原为 D16 冒号格式。

## 存量现状（审计快照 2026-08-27 · G4-1a 更新 2026-08-30）

生产读侧大面积不满足 R1/R4（尤以 `neo4j_client.py` 无 group 读、Canvas 关联查询为甚），逐条清单与分类见审计文档。本契约对**新增代码即刻生效**；存量收敛按审计清单分批移交（G2-3 起）。

**G4-1a 收敛进度（service 层 BLOCKER 面已封堵）**：审计 §5「无 group 读 9 处」中 #8（`get_concept_score_history`）已修；#3（`get_review_suggestions` 无 group 分支）已在**唯一生产调用方**侧封死并加 `logger.error` 哨兵，client 签名收敛移交 G4-1b；#2/#4 两处 CONDITIONAL（alias 部分过滤 / group 依赖可选参数）已升为全 alias 过滤 + 前缀语义。剩余 #11-#14 / #17 / #18 / #19 与 JSON 镜像族 → **CARD-G4-1b**。
