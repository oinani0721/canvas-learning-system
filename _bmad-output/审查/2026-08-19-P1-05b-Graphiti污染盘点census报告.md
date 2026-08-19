# P1-05b 步骤 2 · Graphiti 结构化图污染只读盘点报告

> 生成: 2026-08-19 · 脚本: `backend/scripts/census_graphiti_pollution.py`（commit `da3aeef5`）
> 性质: **只读**（全部 Cypher 为 MATCH/RETURN 计数，routing_="r"，未动库一字）
> 待你批准的事项在 **§5**，其余是数据与解读。

---

## 1. TL;DR

- **真正要隔离的污染比预担忧小得多：`vault__canvas_vault` 组里 active 污染边只有 2 条**（callout 1 条 + relation 1 条），其中 1 条是现有 `invalidate_missing_callouts` 永远够不到的（relation 通道，无 annotation_id）。
- **碰撞体检：1 个碰撞 stem（`CLAUDE`），但补查 Q1b 显示碰撞 stem 命中的 active 边 = 0 条** → 本次隔离**可按 stem 精确定位**，不需要降级到 uuid5 匹配。
- **意外发现①**：图里已存在一个历史隔离组 `quarantine__mem_cleanup`（4 条边）——MEM-FLYWHEEL 清理期的先例，用的是 `quarantine__` 前缀（**不带** vault 前缀），结构上永远不会被检索面的前缀扩展拾取。
- **意外发现②（灰色地带，不在本次隔离范围）**：`vault__canvas_vault` 有 **87 条 active 边挂在 10 个磁盘上不存在的 node_id** 上（文件已删/改名）。这不是"禁区污染"而是"无法从磁盘解释"，需要单独裁定（见 §6.2）。

## 2. 环境与方法

| 项 | 值 |
|---|---|
| vault（磁盘侧扫描） | `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`（live） |
| Neo4j | `bolt://localhost:7691`（现网） |
| 启动回填组（物理） | `vault__canvas_vault` |
| CLI 脚本组（物理） | `vault__default` |
| 磁盘侧禁区判定 | `vault_backfill.is_blacklisted_for_backfill`（与回填**同一函数**，非拷贝） |
| 磁盘侧结果 | 禁区 stem 83 个 · 合法 stem 61 个 |

## 3. 盘点结果

### Q0 组分布（structured_writer 四通道边全景）

| group_id | source | edges |
|---|---|---|
| `quarantine__mem_cleanup` | callout | 3 |
| `quarantine__mem_cleanup` | error | 1 |
| `vault__canvas_vault` | callout | 112 |
| `vault__canvas_vault` | error | 1 |
| `vault__canvas_vault` | relation | 10 |
| `vault__canvas_vault__fundamentals` | error | 1 |
| `vault__default` | callout | 2 |

→ 污染**没有**分散进 `vault__default`（CLI 组干净），主战场就是 `vault__canvas_vault`。

### Q4 碰撞体检（磁盘侧）

- 禁区 stem ∩ 合法 stem = **1 个：`CLAUDE`**
  - 禁区侧: vault 根级 `CLAUDE.md`（root_level 规则）
  - 合法侧: `raw/CS188/CLAUDE.md`（普通子目录）
- **Q1b 补查：碰撞 stem 命中的 active 边 = 0 条** → 碰撞对本次执行无实际影响，**按 stem 定位即精确定位**。

### Q1 爆炸半径（禁区 stem 命中，83 个 stem 参与匹配）

| 组 | source | total | active | active_reconcilable |
|---|---|---|---|---|
| `vault__canvas_vault` | callout | 1 | 1 | 1 |
| `vault__canvas_vault` | relation | 1 | 1 | **0** |
| 其余三组 | — | 0 | 0 | 0 |

→ **可精确定位（非碰撞 stem）：2 条 = 全部**；只能按 stem 近似：0 条。
→ active − reconcilable = **1 条**（relation 通道）是现有对账机制结构性够不到的——这正是"跳过选中 ≠ 失效旧污染"的实证。

### Q2 补集残渣（node_id 无法从磁盘任何 md stem 解释的 active 边）

| 组 | active 边 | 涉及 node_id 数 |
|---|---|---|
| `vault__canvas_vault` | **87** | 10 |
| `quarantine__mem_cleanup` | 4 | 2 |
| `vault__canvas_vault__fundamentals` | 1 | 1 |
| `vault__default` | 0 | 0 |

### Q3 被禁区 stem 命名的 :Entity 节点

`vault__canvas_vault` 1 个 + `quarantine__mem_cleanup` 1 个 = **2 个**。

## 4. 解读

1. **为什么 Q1 这么小**：b5706b04 之前 backfill 的旧黑名单虽绕过硬底，但仍拦了检验白板等主要目录；漏进来的主要是 `.trash/.quarantine/.claude` 三个新硬底目录与根级文件——而这些目录里带 callout/relationship 的 md 本就少。**半径小 ≠ 白干**：那 1 条 relation 边正是不可对账通道的实锤，且写入口不堵住，半径只会随时间长大。
2. **`quarantine__mem_cleanup` 先例**：证明"改 group_id 隔离"手法在本库已实战过一次，且其命名避开了 vault 前缀。
3. **检索面断流机制核对**（代码实读）：`memory_service._search_graphiti` 的组列表 = 主组 + `__semantic` 影子组 + `_expand_vault_subgroups`；后者用 `MATCH (n) WHERE n.group_id STARTS WITH 'vault__canvas_vault__'` 按**节点**枚举。**只改边、不改节点的隔离对两种候选组名都断流**——但若未来任何*节点*落进 `vault__canvas_vault__quarantined`，该组会被自动并回检索面；`quarantine__` 前缀则结构上免疫。

## 5. ⛔ 待你批准 — 步骤 3 隔离执行方案

**目标**：`vault__canvas_vault` 组 Q1 的 2 条 active 污染边（按 stem 精确定位，无误杀风险）。

**手法**（按计划裁定）：裸 Cypher `SET e.group_id = <隔离组>, e.quarantined_reason = 'p105b_admission_backfill_gap', e.quarantined_at = datetime()`——绕开 `EntityEdge.save()` 的 embedding 回载 NPE 陷阱（有 canvas_projection_sync / graphiti_belief_service 两处裸 Cypher 先例）。**不 DELETE、不只设 invalid_at**（`_search_graphiti` 不传 SearchFilters，invalid_at 挡不住语义检索）。

**隔离组名需要你二选一**：

| 选项 | 组名 | 优点 | 风险 |
|---|---|---|---|
| A（计划原裁定） | `vault__canvas_vault__quarantined` | 命名归属清晰（跟着 vault 走） | 前缀在 `_expand_vault_subgroups` 的扫描面内；靠"只改边不改节点"这一纪律保安全（验收门会实测） |
| **B（census 后新建议）** | `quarantine__p105b` | 沿 `quarantine__mem_cleanup` 既有先例；结构上**永远**不可能被前缀扩展并回检索面 | 与 vault 的归属关系只能靠 `quarantined_reason` 字段表达 |

> 我的推荐：**B**。理由：先例一致 + 免疫未来代码演化（不依赖"边/节点纪律"续命）。

**验收门**（执行后立即跑，全量化）：
1. 重跑 census Q1 → `vault__canvas_vault` active 归零
2. `_expand_vault_subgroups("vault__canvas_vault")` 实测返回值不含隔离组
3. 随机抽被隔离边的 node_id 走 `search_memories` → 不再召回

**回滚**：`quarantined_reason` + `quarantined_at` 双字段在位，一条 Cypher 可整批还原。

## 6. 附带发现（登记，不在本轮擅动）

1. **backfill 与统一准入的已知差异**：`is_blacklisted_for_backfill` 只判目录 + 根级，**不查文件名黑名单**（`DEFAULT_VAULT_SKIP_FILES`）——所以 `raw/CS188/CLAUDE.md`（系统文档）的 callout 会被 backfill 回填进图；而四条新链的 `check_vault_path` 会以 `blacklisted_file` 拦下同一文件。是否让 backfill 对齐统一准入，牵动其 22 条契约锁，留待你裁定。
2. **Q2 的 87 条残渣**：挂在 10 个磁盘上不存在的 node_id 上。可能来源：①实时批注通道写入的 node_id 与文件 stem 不同构；②节点文件删除/改名后的遗边。census 按计划不输出明细；若你要裁定，我可以出一份"只含 node_id 与计数、不含 fact 正文"的补充清单。
3. **`vault__canvas_vault__fundamentals` 组的 1 条 error 边**：白板级子组的正常写入位置，其 node_id 磁盘不可解释（归入 Q2 类），随 §6.2 一并裁。

---

*步骤 1（四链准入）已完成并独立提交（`66895474`）；步骤 2 本报告对应 commit `da3aeef5`。步骤 3 等你批准后执行。*
