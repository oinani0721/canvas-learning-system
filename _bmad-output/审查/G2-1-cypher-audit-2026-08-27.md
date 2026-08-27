# G2-1 Cypher 读写契约审计清单（2026-08-27）

> **BATCH-2026-08-27-第四批 / CARD-G2-1** ｜ 契约规则: `.claude/rules/cypher-read-contract.md`（R1-R5）/ `.claude/rules/cypher-write-contract.md`（W1-W5）｜ 真库门测试: `backend/tests/integration/test_cypher_contract_gate.py`
> 审计执行: Claude（10 个并行分类 agent + 主循环 100% 覆盖对账 + 6 处人工抽查）；分类正确性另经 Codex 独立抽查（见 `codex-review-CARD-G2-1.md`）。

## §1 方法论与宇宙口径

**grep 口径**（2026-08-27 于本 worktree 实测）:

| 面 | 模式 | 范围 | 实测 | 说明 |
|---|---|---|---|---|
| A | `.run_query(` / `.execute_query(` | `backend/app`（除 `clients/neo4j_client.py` 本体） | **75** | 与卡片勘探"75 处"一致；含 7 处注释/docstring 引用（表内标 NON-QUERY） |
| B | `session.run(` / `tx.run(` | `backend/app` | **24** | 含 `cypher_helpers.py` docstring 3 处伪引用（NON-QUERY） |
| C | 上述四模式合并 | `backend/scripts` + 根 `scripts/` | **40** | backend/scripts 33 + 根 scripts 7；文件级粗分类 |
| D | 方法内 Cypher 语句逐条 | `backend/app/clients/neo4j_client.py` | **19 条** | 语句级精分类（§5），与 A/B 的调用点口径不同 |

未发现 `execute_read(` / `execute_write(` / `read_transaction(` / `write_transaction(` 用法（grep 0 命中）。`backend/migrations/*.cypher` 为 DDL 迁移文件，不在运行时调用面。

**分类深度声明（如实）**: A/B 面 99 处调用点逐条精分类（读到实际 Cypher 文本与参数绑定后判定）；C 面 8 个文件为**文件级粗分类，未逐条精判**（每个文件的 note 中已如实标注）；D 面 19 条语句逐条精分类。分类由 10 个并行 agent 产出，主循环做了 99/99 覆盖对账（零缺失/零多余/零重复）与 6 处人工抽查（§8）。

## §2 `cypher_with_group_filter` 调用点 100% 枚举

**结论：生产调用 = 0。** 全量引用（grep `cypher_with_group_filter`，含 md/yml）:

| 类别 | 位置 | 性质 |
|---|---|---|
| helper 本体 | `backend/app/utils/cypher_helpers.py:99` | `def cypher_with_group_filter(` 定义 |
| helper 自述 | `cypher_helpers.py:4,21,26,72,131,138` | docstring/backlog 备忘（非调用） |
| 生产**显式拒用** | `backend/app/services/verification_service.py:2117` | 注释："不用 cypher_with_group_filter(): 该 helper 单 alias 启发式注入, 这里两条查询要同时过滤 b/n/m 三个 alias…手写 WHERE" |
| 单元测试 | `backend/tests/unit/test_cypher_helpers.py:4,20,25,31,36,41,45,51,58,64,70,81,90,96,101,107,117,123,168,180,209,211` | 测试 helper 字符串注入行为（22 处引用） |
| 单元测试 | `backend/tests/unit/test_lancedb_isolation_assertions.py:33,78,81,147,152` | 链路一致性断言（5 处引用） |
| lint 文案 | `lefthook.yml:135` | cypher-vault-filter-lint 的修复建议文案 |
| 文档 | 根 `CLAUDE.md:40` | "必须用 cypher_with_group_filter()" — **与实况矛盾的过时条款**（矛盾记录见两份契约规则文档；改 CLAUDE.md 本体 = 移交，不在本卡） |

**helper 两大局限（真库实证，2026-08-27 于 7692 测试容器 EXPLAIN 实测）**:
1. 单 alias 启发式注入 — 多 alias 查询无法覆盖（verification_service.py:2117 拒用的直接原因）；
2. MERGE/CREATE 开头查询注入产生**非法 Cypher**: `cypher_with_group_filter("MERGE (n:Concept {name: $name}) RETURN n", gid)` → `" WHERE n.group_id = $group_id MERGE …"` → `Neo.ClientError.Statement.SyntaxError: Invalid input 'WHERE'`。此局限已在门测试 `test_helper_merge_lead_limitation_documented` 固化为行为证据。

## §3 backend/app `.run_query()` / `.execute_query()` 75 处精分类

判定分布: COMPLIANT 44 / CROSS-VAULT-BY-DESIGN 6 / CONDITIONAL 15 / VIOLATION 6 / NON-QUERY 4

| 位置 | 函数 | 类型 | op | 涉及标签 | group scope | 物理化 | 契约 | 判定 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| `api/v1/endpoints/edges.py:106` | `_write_neo4j_triplet` | call | write | EdgeRationale | filtered | yes | W1:ok,W3:ok | **COMPLIANT** | CREATE :EdgeRationale 属性含 group_id(to_physical_group_id 物理化, resolved_group_id 由 endpoint 顶部 resolve_vault_group_id 派生); record_id 为新 uuid, append-only 时序设计, 无 MERGE 按 name 冲撞面 |
| `api/v1/endpoints/exam_sessions.py:175` | `list_exam_sessions` | call | read | EpisodicNode | filtered | yes | R1:ok,R4:ok,R5:ok | **COMPLIANT** | e.group_id 等值过滤恒在; vault_id→build_vault_group_id, 缺失时 fallback deprecated group_id 或 DEFAULT_GROUP_ID 均有 logger.warning(非静默), 最终 to_physical_group_id 物理化; board_filter 为固定字符串+$board_id 参数, 无注入面 |
| `api/v1/endpoints/health.py:157` | `health_check` | call | ping | (无节点) | na | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | RETURN 1 AS ping 连通性探针, 不触碰任何业务节点; mode-aware 4 态分类(NEO4J ok/degraded/JSON_FALLBACK/unavailable)有大段注释声明意图, 属 R2 允许的系统健康类 |
| `api/v1/endpoints/profile.py:230` | `get_profile_tips` | call | read | EntityNode, EpisodicNode | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 锚点 n.group_id 等值过滤 + to_physical_group_id 物理化; 两点残余风险: (1) 关联端 e:EpisodicNode 未单独过滤, 依赖关系不跨 group 的隐含前提; (2) group_id Query 默认 DEFAULT_GROUP_ID(deprecated cs188), 调用方漏传时静默落错 namespace(仍过滤, 非全库扫描)。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `api/v1/endpoints/profile.py:299` | `get_profile_weaknesses` | call | read | EntityNode, (无标签 e) | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 同 tips 模式: n.group_id 等值过滤 + 物理化; 关联端 e 无标签且未过滤 group(依赖边不跨 group 前提), 默认 group_id 落 DEFAULT_GROUP_ID 同上。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `api/v1/endpoints/profile.py:357` | `get_profile_qa_highlights` | call | read | EntityNode, EpisodicNode | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 同 tips 模式: n.group_id 等值过滤 + 物理化; e 侧未单独过滤、默认 DEFAULT_GROUP_ID 两点残余风险同上。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `api/v1/endpoints/subjects.py:137` | `list_subjects` | call | read | Subject, CanvasNode | filtered | yes | R1:ok,R2:ok,R5:ok | **COMPLIANT** | :Subject 列表全局(vault 无关元数据, 文件头 P0-SYNC-ISO R10 注释显式声明); CanvasNode 计数侧带等值 OR 前缀双条件 group 过滤, 参数经 _resolve_read_group_params → to_physical_group_id 物理化, 无 vault_id 时 fallback 激活 vault(有 warning) |
| `api/v1/endpoints/subjects.py:192` | `create_subject` | call | read | Subject | absent | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | 重名检查 MATCH (s:Subject {name}) 全局扫描; :Subject 是 vault 无关全局用户配置(文件头注释声明, 节点本身不写 group_id), 名称唯一性跨 vault 生效属设计意图 |
| `api/v1/endpoints/subjects.py:202` | `create_subject` | call | write | Subject | absent | na | W1:na,W4:ok | **CROSS-VAULT-BY-DESIGN** | CREATE :Subject 不带 group_id — 文件头注释显式声明 Subject 为全局元数据(与 subject_config.list_subjects CROSS-VAULT BY DESIGN 定位一致); id 为新 uuid 无冲撞面, 且 CREATE 非 MERGE |
| `api/v1/endpoints/subjects.py:277` | `update_subject` | call | read | Subject | absent | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | HIGH-2 重名检查(排除自身 id)全局扫描 :Subject; 同 create_subject, 全局元数据设计意图有文件头注释背书 |
| `api/v1/endpoints/subjects.py:303` | `update_subject` | call | write | Subject | id-scoped | na | W5:ok | **COMPLIANT** | MATCH (s:Subject {id: $subject_id}) SET — 按全局唯一 subject_id(subj_+uuid12) 点更, 满足 W5 唯一 ID scope; set_clause 只拼固定属性名, 值全走参数, 无注入面(HIGH-3 注释) |
| `api/v1/endpoints/subjects.py:325` | `update_subject` | call | read | CanvasNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | node_count 查询带 _CANVAS_NODE_GROUP_FILTER(等值 OR '__'定界前缀), group 参数已 to_physical_group_id 物理化, P0-SYNC-ISO R10 读侧隔离修复到位 |
| `api/v1/endpoints/subjects.py:366` | `delete_subject` | call | delete | Subject | id-scoped | na | W2:ok | **COMPLIANT** | DELETE 按全局唯一 subject_id 点删, 满足 W2 唯一 ID scope; 软删只删 :Subject 元数据节点, 不碰 CanvasNode/CanvasBoard |
| `clients/neo4j_edge_client.py:149` | `Neo4jEdgeClient.add_edge_relationship` | docstring | na | na | na | na | NON-QUERY | **NON-QUERY** | 方法 docstring 里的 Story 36.1 说明文字, 非真调用; 实际实现委托 self._neo4j.create_edge_relationship()。 |
| `clients/neo4j_edge_client.py:281` | `Neo4jEdgeClient.search_nodes` | call | read | (无标签 MATCH (n) — 实际命中 Node/EntityNode) | conditional | yes | R1:conditional,R4:silent-fallback,R5:ok | **CONDITIONAL** | CONTAINS 兜底路径: group_id 为可选参数, 传入时 WHERE n.group_id=$groupId 且过 to_physical_group_id; 不传则无 group 过滤, 无标签 MATCH (n) 全图文本扫 = R4 静默跨 vault 退化。 |
| `clients/neo4j_edge_client.py:370` | `Neo4jEdgeClient._search_nodes_fulltext` | call | read | fulltext index node_search_unified (Node/EntityNode) | conditional | yes | R1:conditional,R4:silent-fallback,R5:ok | **CONDITIONAL** | fulltext 快路径: group_id 有传才加后置 WHERE 过滤(且已 to_physical); 不传则 queryNodes 结果跨全部 vault 返回, 与 281 行同一 CONDITIONAL 形态。 |
| `clients/neo4j_edge_client.py:436` | `Neo4jEdgeClient.get_related_memories` | call | read | Node, CONNECTS_TO | id-scoped | na | R1:violation(R3 不适用) | **VIOLATION** | 按 {id:$nodeId} 点查关联节点(可选 canvas_path 过滤)。canvas node id 属 R3 反例(可外部传入/缺失时仅取 UUID 前 8 位, 复制 canvas 撞 id, 唯一性不可证), 且 Node/CONNECTS_TO legacy 图无 group 属性可滤 — 与 §5 #11-14 同型, VIOLATION(R1; R3 不适用)。【Codex round-2 升级, round-3 清除矛盾旧句】 |
| `clients/neo4j_learning_base.py:113` | `Neo4jLearningBase (class docstring)` | docstring | na | na | na | na | NON-QUERY | **NON-QUERY** | 类 docstring 中的用法示例注释 'Use self._neo4j.run_query()', 非真调用。 |
| `clients/neo4j_learning_base.py:209` | `Neo4jLearningBase.add_edge_relationship (abstract)` | docstring | na | na | na | na | NON-QUERY | **NON-QUERY** | 抽象方法 docstring 的实现指引文字, 非真调用。 |
| `clients/neo4j_learning_base.py:243` | `Neo4jLearningBase.search_nodes (abstract)` | docstring | na | na | na | na | NON-QUERY | **NON-QUERY** | 抽象方法 docstring 的实现指引文字, 非真调用。 |
| `services/agent_service.py:1977` | `AgentService._record_color_transition` | call | write | EntityNode (entity_type=ColorTransition) | filtered | yes | W1:ok,W3:ok | **COMPLIANT** | CREATE ColorTransition 节点带 group_id, 绑定值 to_physical(canonical(ContextVar) or DEFAULT_GROUP_ID); ContextVar 优先防跨 vault 泄漏(wave-5 P0 修复), 缺失退默认组而非无 group。 |
| `services/agent_service.py:2198` | `AgentService._query_neo4j_memories` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | WHERE m.group_id=$group_id 恒过滤 + CONTAINS 文本匹配, group_id 走 to_physical(canonical(ContextVar) or DEFAULT_GROUP_ID), 与 _record_color_transition 写侧成对; 无 group 缺失分支。 |
| `services/canvas_projection_sync.py:159` | `CanvasProjectionSync.sync_reason_edges (幽灵边对账)` | call | write | CANVAS_EDGE | filtered | yes | W2:ok,W5:ok,W3:ok | **COMPLIANT** | 软失效更新 WHERE e.group_id=$group_id AND synced_from='frontmatter' 全程 group 收束, physical_gid 经 to_physical; group 缺省回退 build_vault_group_id(当前 vault)(T2 注释声明), 非全库; alive_ids/protected 前缀豁免防误杀。 |
| `services/canvas_projection_sync.py:241` | `CanvasProjectionSync._merge_edge` | call | write | CanvasNode, CANVAS_EDGE | filtered | yes | W1:ok,W3:ok,W5:ok | **COMPLIANT** | MERGE 身份键均为 {id, group_id} 复合键(P0-SYNC-ISO-2026-08-17 三方一致切换), edge_id 亦含 physical_gid 前缀防跨 vault 同名节点对共享 id; group_id 全程 to_physical 物理化。 |
| `services/conversation_inheritance.py:124` | `_fetch_neighbor_records_for_inheritance` | call | read | EntityNode | absent | na | R1:violation | **VIOLATION** | MATCH (n:EntityNode)-[r]-(neighbor:EntityNode) WHERE n.name = $node_id OR n.mastery_concept_id = $node_id 完全无 group_id 过滤; n.name 按名匹配非全局唯一 (R3 不适用), neighbor 侧也无 scope — 跨 vault 同名节点的邻居与关系会泄入对话继承上下文; 调用方 (line 67) 明明已解析 group_id 却未下传此查询 |
| `services/exam_service.py:308` | `_get_canvas_type` | call | read | EpisodicNode | id-scoped | na | R3:ok | **COMPLIANT** | 按 e.uuid = $canvas_id 点查 count 且附加 source_description='exam_session' 过滤; uuid 全局唯一, R3 免 group 过滤, 无 group_id 绑定故无物理化问题 |
| `services/exam_service.py:368` | `_persist_session_to_neo4j` | call | write | EpisodicNode | id-scoped | yes | W1:ok,W3:ok | **COMPLIANT** | MERGE 身份键为全局唯一 session uuid (W1 经唯一 ID 满足), group_id 经 to_physical_group_id 物理化 (W3 ok); 风险: group_id 恒写 DEFAULT_GROUP_ID 而非会话实际 vault — 多 vault 下所有 exam session 挤同一默认组, vault 归属缺失 |
| `services/exam_service.py:399` | `_load_session_from_neo4j` | call | read | EpisodicNode | id-scoped | na | R3:ok | **COMPLIANT** | MATCH (e:EpisodicNode {uuid: $exam_id}) 全局唯一 exam_id 点查 + source_description 过滤, R3 免 group 过滤 |
| `services/exam_service.py:422` | `_load_sessions_by_canvas_from_neo4j` | call | read | EpisodicNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | 带 e.group_id 等值过滤且经 to_physical_group_id 物理化; 但过滤值恒为 DEFAULT_GROUP_ID 非请求 vault — 与写侧 (line 368) 一致故当前读写闭环, 若写侧未来改按 vault 写组则此处静默漏读; source_board_id 跨 vault 撞名时同组内仍可混 |
| `services/exam_service_ext.py:99` | `sync_node_to_source_canvas` | call | write | CanvasNode | filtered | yes | W1:ok,W3:ok | **COMPLIANT** | MERGE (n:CanvasNode {id,group_id}) 复合键 (P0-SYNC-ISO 2026-08-17 升级), group_id 在 L65 经 to_physical_group_id; 唯一残留风险是 group_id 参数默认 DEFAULT_GROUP_ID (deprecated cs188 fallback), 调用方漏传时写入落错 vault |
| `services/exam_service_ext.py:148` | `sync_node_to_source_canvas` | call | write | CanvasNode, EXAM_DISCOVERED | filtered | yes | W1:partial,W3:ok,W5:partial | **CONDITIONAL** | 两端点 MATCH 均带 {id,group_id} 复合限定, 边属性 r.group_id 物理化写入; 空匹配 (跨 group 端点) 有显式检测降 edge_created=False, 不静默借端点。【Codex round-3 整改 2026-08-27】边 MERGE 身份键仅 {relation_type}, group_id 为后置 SET — 端点虽双双 group 锁定, 但同端点间已存在的错组/NULL 组存量边可被 MERGE 命中并覆写, 按'关系不跨组前提不可证'严格口径降 CONDITIONAL（写侧边键正例见 sync_service.py:578 的 {id, group_id} 复合边键） |
| `services/exam_service_ext.py:196` | `sync_node_to_source_canvas` | call | read | EpisodicNode | id-scoped | na | R3:ok | **COMPLIANT** | 深度链回溯读: WHERE source_description='discovered_node' AND node_id AND source_exam_id — exam_id 全局唯一, node_id 在 exam 范围内限定, 免 group 过滤合规 |
| `services/exam_service_ext.py:227` | `sync_node_to_source_canvas` | call | write | EpisodicNode | id-scoped | yes | W1:ok,W3:ok | **COMPLIANT** | MERGE 键 uuid=disc_{exam_id}_{node_id} 由全局唯一 exam_id 派生, 免复合 group 键; d.group_id 属性经 L65 物理化写入 |
| `services/exam_service_ext.py:483` | `skip_question` | call | read | EpisodicNode | id-scoped | na | R3:ok | **COMPLIANT** | 按 uuid=$exam_id + source_description='exam_session' 点查读 skipped_nodes, exam_id 全局唯一, R3 免 group 过滤 |
| `services/exam_service_ext.py:502` | `skip_question` | call | write | EpisodicNode | id-scoped | na | W5:ok | **COMPLIANT** | MATCH {uuid,source_description} SET skipped_nodes — 更新 scope 为全局唯一 uuid, 无 group_id 写入故无物理化需求 |
| `services/exam_service_ext.py:560` | `_update_exam_lifecycle_status` | call | write | EpisodicNode | id-scoped | na | W5:ok | **COMPLIANT** | pause/resume 状态更新, MATCH {uuid:$exam_id,source_description:'exam_session'} 全局唯一 ID scope, 合规 |
| `services/exam_service_ext.py:660` | `complete_exam` | call | write | EpisodicNode | id-scoped | yes | W1:ok,W3:ok | **COMPLIANT** | MERGE {uuid:$exam_id} 全局唯一键, group_id L610 物理化后 SET; 注意: 该 MERGE 无 source_description 限定会命中同 uuid 的 exam_session 节点并改写为 exam_record (数据模型怪癖非 vault 违规), 且 group_id 默认 DEFAULT_GROUP_ID fallback |
| `services/exam_service_ext.py:704` | `complete_exam` | call | write | EpisodicNode | id-scoped | na | W5:ok | **COMPLIANT** | session 收尾更新 MATCH {uuid,source_description:'exam_session'} 唯一 ID scope; 因 L660 MERGE 已把该节点 source_description 改成 exam_record, 此句实际常空匹配 (非隔离问题) |
| `services/exam_service_ext.py:772` | `get_exam_records` | call | read | EpisodicNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | count 查询 WHERE e.group_id=$group_id AND source_description='exam_record', group_id 在 L744 物理化; 默认 DEFAULT_GROUP_ID 仍过滤不退化全库扫描 |
| `services/exam_service_ext.py:778` | `get_exam_records` | call | read | EpisodicNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | 分页 list 查询与 count 同 WHERE group_id 等值过滤 (L744 物理化), 输出不含 group_id 字段故无 desanitize 需求 |
| `services/exam_service_ext.py:816` | `get_exam_record` | call | read | EpisodicNode | id-scoped | na | R3:ok | **COMPLIANT** | 按 uuid=$exam_id 点查 exam_record 详情, R3 免 group 过滤; 函数签名接收 group_id 参数但完全未用 — 已知 exam_id 可读任意 vault 记录, ID 全局唯一前提下可接受但参数名实不符 |
| `services/exam_service_ext.py:878` | `get_records_by_canvas` | call | read | EpisodicNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | WHERE e.group_id=$group_id AND source_canvas_id=$canvas_id, group_id 在 L856 物理化; 默认 DEFAULT_GROUP_ID fallback 同 L772 备注 |
| `services/fallback_sync_service.py:352` | `FallbackSyncService._replay_scoring_entry_to_neo4j` | call | write | User, Concept, LEARNED | absent | conditional (group_id 为空时原样传递) | W1:violation,W3:conditional,W5:violation | **VIOLATION** | MERGE (c:Concept {name:$concept}) 仅按 name 合并 — 跨 vault 同名概念冲撞成同一节点, 后续 SET c.group_id=$groupId last-write-wins 劫持节点归属; r:LEARNED 更新 scope 同样无 group; 另 to_physical 有条件短路(group_id 为 None 时写 null group_id)。 |
| `services/fallback_sync_service.py:458` | `FallbackSyncService._replay_learning_memory_to_neo4j` | call | write | User, Concept, LEARNED | absent | conditional (group_id 为空时原样传递) | W1:violation,W3:conditional,W5:violation | **VIOLATION** | 与 352 行同形: MERGE Concept 仅按 name, 跨 vault 同名冲撞 + SET c.group_id/r.group_id last-write-wins 覆盖; 额外 SET r.next_review 使 FSRS 复习状态也被跨 vault 串写; _build_group_id_from_canvas 可返回 None → groupId=null。 |
| `services/graphiti_belief_service.py:108` | `_ensure_belief_key_index` | call | schema | RELATES_TO (关系属性索引 canvas_belief_key) | na | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | CREATE INDEX IF NOT EXISTS 幂等建索引, schema DDL 天然全库; docstring 明确声明 best-effort 优化意图(无 @allow_cross_vault 装饰器, 但意图注释充分)。 |
| `services/graphiti_belief_service.py:132` | `_query_edges_by_belief_key` | call | read | Entity, RELATES_TO | filtered | conditional (sanitize 不做 legacy canonicalization) | R1:ok,R5:partial | **CONDITIONAL** | WHERE e.group_id=$group_id AND e.belief_key=$belief_key, group_id 为必传参数, routing_='r'; 但调用方物理化走 sanitize_group_id_for_graphiti 而非 to_physical_group_id — vault: 输入等价, 遗留裸值(如 cs188)不做 canonical 映射; 与本文件写侧同一 gid, 读写自洽。【Codex R5 整改 2026-08-27】note 原已标 R5:partial 但 verdict 误留 COMPLIANT, 与 memory_service:1697 同因(sanitize 不做 legacy canonicalization)统一降 CONDITIONAL |
| `services/learning_context_service.py:105` | `_fetch_mastery` | call | read | EntityNode | absent | na | R1:violation, R3:n/a(name 非全局唯一) | **VIOLATION** | fallback 查询完全无 group_id 过滤, 而函数明明持有 group_id 形参未绑定; n.name = $cid 跨 vault 同名概念可命中他 vault 的 EntityNode 并把其 name 注入上下文(mastery_concept_id 或许唯一但 OR name 分支破坏 R3 前提)。 |
| `services/learning_context_service.py:387` | `_fetch_neighbor_records` | call | read | EntityNode, 任意关系类型 [r] | conditional | yes | R1:conditional(NULL-group legacy 豁免), R5:ok | **CONDITIONAL** | 两端点都过滤 (group_id = $gid OR group_id IS NULL), gid 经 to_physical_group_id 物理化; 但 OR IS NULL 分支让无主 legacy 节点同时出现在所有 vault 的邻居结果里(docstring 已声明向后兼容意图), 属过滤依赖分支的弱化；未过滤的关系 r 的 reason/label 字段被直接返回进上下文（round-3 补记） |
| `services/mastery_store.py:58` | `get_concept` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | WHERE n.group_id=$group_id AND (mastery_concept_id OR name) LIMIT 1; group_id 经 to_physical_group_id (L48)。默认参数 DEFAULT_GROUP_ID(cs188 弃用组) 调用方漏传会静默落入弃用组, 但仍过滤非全库扫描。 |
| `services/mastery_store.py:95` | `save_concept` | call | write | EntityNode | filtered | yes | W1:ok,W3:ok | **COMPLIANT** | MERGE 身份键为 {group_id, mastery_concept_id} 复合键, props["group_id"] 与 MERGE 键同源均已物理化 (L84-86), 无跨 vault 同名冲撞。 |
| `services/mastery_store.py:123` | `get_all_concepts` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | 组内全量读 (WHERE n.group_id=$group_id AND p_mastery IS NOT NULL), group_id 物理化 (L114)。 |
| `services/mastery_store.py:194` | `record_interaction_event` | call | write | EntityNode | filtered | yes | W5:ok,W3:ok | **COMPLIANT** | MATCH {group_id, mastery_concept_id} 复合 scope 后 SET 交互事件属性, 匹配绑定的 group_id 已物理化 (L186)。 |
| `services/mastery_store.py:222` | `record_override_event` | call | write | EntityNode | filtered | yes | W5:ok,W3:ok | **COMPLIANT** | MATCH {group_id, mastery_concept_id} 复合 scope 后 SET override 属性, group_id 物理化 (L213)。 |
| `services/mastery_store.py:255` | `find_concept_by_name` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | 模糊名称 CONTAINS 查询但先按 n.group_id=$group_id 等值过滤, LIMIT 1, group_id 物理化 (L244), 模糊匹配限定在 vault 内。 |
| `services/mastery_store.py:312` | `get_board_concepts` | call | read | Canvas, CONTAINS_NODE, Node, EntityNode | filtered | yes | R1:violation,R5:ok | **VIOLATION** | 违反 R1(部分): MATCH (c:Canvas)-[:CONTAINS_NODE]->(n:Node) 段仅按 c.path 匹配无 group 过滤——Canvas 节点在 neo4j_client.py:1072/1115/1288 仅按 {path} MERGE 本身无 group_id, 跨 vault 同名 canvas path 会把他 vault 的 node_ids 混入 collect(), 板级归属可被跨 vault 污染; 最终 EntityNode 段有 group 过滤故返回数据仍限本组。另有 L337 空结果时静默退化为组内全量 get_all_concepts(板级→组级放宽, docstring 已声明)。 |
| `services/mastery_store.py:361` | `record_self_assess_event` | call | write | EntityNode | filtered | yes | W5:ok,W3:ok | **COMPLIANT** | MATCH {group_id, mastery_concept_id} 复合 scope 后 SET 自评属性, group_id 物理化 (L353)。 |
| `services/mastery_store.py:398` | `save_calibration_record` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | read-modify-write 的读步: WHERE group_id AND (mastery_concept_id OR name) LIMIT 1, group_id 物理化 (L386) 与写步共用。 |
| `services/mastery_store.py:428` | `save_calibration_record` | call | write | EntityNode | filtered | yes | W5:ok,W3:ok | **COMPLIANT** | 写步 MATCH...SET 带 group_id 过滤符合 W5; 小风险(vault 内非跨 vault): 匹配条件 (mastery_concept_id=$node_id OR name=$node_id) 无 LIMIT, 组内 name 撞 node_id 时会多节点同时被 SET 校准记录。 |
| `services/mastery_store.py:473` | `get_calibration_records` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | WHERE group_id AND (mastery_concept_id OR name) AND records IS NOT NULL LIMIT 1, group_id 物理化 (L464)。(非契约项: docstring 称错误时返回空表但此方法无 try/except。) |
| `services/mastery_store.py:520` | `get_dangerous_nodes` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | 危险盲点列表读取, WHERE n.group_id=$group_id AND is_dangerous=true, group_id 物理化 (L511)。 |
| `services/memory_service.py:256` | `ensure_fulltext_index` | call | schema | EpisodicNode (fulltext index episode_content) | na | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | CREATE FULLTEXT INDEX IF NOT EXISTS 的 DDL, vault 无关的 schema 巡检; docstring 明确声明启动时自动建索引意图(无 @allow_cross_vault 装饰器但注释充分)。 |
| `services/memory_service.py:1451` | `find_episode_by_content_hash` | call | read | Episodic | filtered | yes | R1:ok, R4:ok, R5:ok | **COMPLIANT** | e.group_id = $group_id 等值过滤且 to_physical_group_id(group_id or DEFAULT_GROUP_ID) 物理化, 缺省退到 vault:default 组而非全库扫描; 残余风险: 调用方漏传 group_id 时幂等判定查错组 → fail-open 可能重复建 episode(重复优于丢数据, 已注释)。 |
| `services/memory_service.py:1697` | `_expand_vault_subgroups` | call | read | 无标签 MATCH (n) — 仅返回 group_id 值 | filtered | conditional (sanitize 不做 legacy canonicalization) | R1:ok,R5:partial | **CONDITIONAL** | STARTS WITH vault__x__ 前缀枚举白板级子组(punycode), 非等值但只能命中本 vault 前缀, 不跨 vault; 入参 _gid_phys 由调用方 sanitize_group_id_for_graphiti 物理化; 无标签全节点扫描仅返回 DISTINCT group_id, LIMIT 50 + 5min 缓存, 无业务数据泄漏。【Codex R5 整改 2026-08-27】绑定链为 sanitize_group_id_for_graphiti(非 to_physical_group_id), legacy cs188 无冒号输入原样直通不做 canonicalization(group_id_compat.py:64-87 vs 140-185), R5 降 partial → CONDITIONAL |
| `services/memory_service.py:1845` | `_search_neo4j_fulltext` | call | read | EpisodicNode (fulltext index episode_content) | conditional | yes | R1:conditional, R4:violation, R5:ok | **CONDITIONAL** | WHERE ($group_ids IS NULL OR node.group_id IN $group_ids) — group_id 不传即静默全索引无过滤扫描, 正是 R4 禁止的可选参数分支; 且实际被踩中: learning_context_service._fetch_tips_and_errors 调 search_memories 未传 group_id。传参时物理化+影子组扩展+输出 desanitize 都正确。 |
| `services/question_generator.py:985` | `_get_kg_relevance` | call | read | CanvasNode, CANVAS_EDGE, RELATES_TO | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 主节点与 neighbor 双侧均限定 group_id = vault_group 或 STARTS WITH vault_prefix (P0-SYNC-ISO R10), _physical_vault_scope 内经 to_physical_group_id 物理化; 另有 {id, canvasId} 复合绑定与墓碑边过滤, 节点侧过滤实现。【Codex round-2 整改 2026-08-27】r:CANVAS_EDGE\|RELATES_TO 关系自身带 group_id 属性未过滤 — 按 R1 严格口径降 CONDITIONAL（缓解: CanvasNode/CANVAS_EDGE 写侧已复合键化, 风险低于 Concept/LEARNED 面） |
| `services/react_agent.py:217` | `search_knowledge_graph (tool)` | call | read | EntityNode | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | WHERE n.group_id=$group_id 恒过滤, 绑定值过 to_physical_group_id(_resolve_effective_group_id()); ContextVar 缺失退 DEFAULT_GROUP_ID 但带 warning(非静默全库)。旁注: entity_types 用 f-string 拼进 Cypher, 是注入面(非本契约条款)。 |
| `services/react_agent.py:372` | `record_learning_memory (tool)` | call | write | EntityNode | filtered | yes | W1:ok,W3:ok | **COMPLIANT** | CREATE 新 EntityNode 带 group_id 属性(to_physical 物理化, 与 217 行读侧成对); node_id=agent-{timestamp} 每次新建无合并冲撞; ContextVar 缺失退 DEFAULT_GROUP_ID 写入 vault__default(带 warning)。 |
| `services/recommendation_service.py:193` | `_count_nodes` | call | read | CanvasNode | filtered | yes | R1:ok, R5:ok | **COMPLIANT** | count 查询 MATCH map 形式 {canvasId, group_id} 等值过滤; group_id 上游经 _resolve_physical_group_id → to_physical_group_id 物理化, 缺省时退到 request ContextVar 而非无过滤。 |
| `services/recommendation_service.py:213` | `_get_unconnected_nodes` | call | read | CanvasNode, CANVAS_EDGE | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 主 MATCH 带 {canvasId, group_id}; 内层 EXISTS 邻居未限组但只用于排除(跨vault脏边会让节点被保守排除, 不泄漏数据); 墓碑边 invalidated_at 已处理。【Codex round-2 整改 2026-08-27】EXISTS 子查询的匿名端点与边 e 未限组 — 跨 vault 脏边会让孤立节点被误判已连接而漏出推荐面, 降 CONDITIONAL |
| `services/recommendation_service.py:246` | `_detect_graph_patterns` | call | read | CanvasNode, CANVAS_EDGE | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 端点 a/b 带 {canvasId, group_id} 且 shared.group_id = $group_id 显式过滤(带意图注释); 残留小缺口: *1..2 变长路径的中间过渡节点(非 shared)未查组, 依赖边不跨 vault 的数据假设。【Codex round-2 整改 2026-08-27】*1..2 变长路径的中间过渡节点与 es1/es2 边未查组('依赖边不跨 vault'假设在 W1 修复前不可证), 降 CONDITIONAL；NOT EXISTS 的 live:CANVAS_EDGE 排除边亦未过滤 group（round-3 补记） |
| `services/recommendation_service.py:278` | `_get_node_titles` | call | read | CanvasNode | filtered | yes | R1:ok, R5:ok | **COMPLIANT** | 标题查询 {canvasId, group_id} 等值过滤, group_id 为已物理化形参(docstring 明示 PHYSICAL vault__x)。 |
| `services/recommendation_service.py:300` | `_get_existing_edge_labels` | call | read | CanvasNode, CANVAS_EDGE | filtered | yes | R1:partial,R5:ok | **CONDITIONAL** | 边 label 建议池查询两端点都带 group_id 过滤(注释明示跨 vault 边不得贡献建议), 墓碑边排除。【Codex round-2 整改 2026-08-27】两端点已过滤但边 e 自身 group_id 未过滤, 按 R1 严格口径降 CONDITIONAL |
| `services/targeting_material_service.py:163` | `collect_targeting_material` | call | read | CanvasNode, CANVAS_EDGE | filtered | yes | R1:ok,R5:ok | **COMPLIANT** | n/e/m 三侧 group_id 严格等值过滤 (IS NULL 放行洞已在 MEM-FLYWHEEL 批次1'② 移除), group_id 为必填参数并经 to_physical_group_id 物理化, 幽灵边 invalidated_at 过滤到位 |
| `services/verification_service.py:2151` | `fetch_connected (in _get_graph_context_for_concept)` | call | read | CanvasBoard, CanvasNode, CANVAS_EDGE | filtered | yes | R1:partial,R4:ok,R5:ok | **CONDITIONAL** | by-name 串库查询 b/n/m 三 alias 全部限定 groupVault =/前缀 (P0-SYNC-ISO R10); _vault_scope_params 经 to_physical_group_id 物理化, group_id 缺省走 ContextVar 兜底且无上下文时收敛为不存在组返回空 (fail-closed, 非全库退化, R4 满足)。【Codex round-2 整改 2026-08-27】b/n/m 三节点 alias 全过滤但 r:CANVAS_EDGE 未过滤且返回 r.label — 节点 alias 覆盖仍是多 alias 手写 WHERE 的形态参考, 关系过滤缺口降 CONDITIONAL |
| `services/verification_service.py:2181` | `fetch_siblings (in _get_graph_context_for_concept)` | call | read | CanvasBoard, CanvasNode | filtered | yes | R1:ok,R4:ok,R5:ok | **COMPLIANT** | 同 fetch_connected: b/n 双 alias 限定 groupVault =/前缀, scope 参数经 _vault_scope_params 物理化且缺省 fail-closed; by-name 同名白板跨 vault 污染已被此过滤挡住 |

## §4 backend/app `session.run()` / `tx.run()` 24 处精分类

判定分布: COMPLIANT 10 / CROSS-VAULT-BY-DESIGN 10 / CONDITIONAL 1 / NON-QUERY 3

| 位置 | 函数 | 类型 | op | 涉及标签 | group scope | 物理化 | 契约 | 判定 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| `api/v1/endpoints/health.py:733` | `_test_neo4j_connection` | call | ping |  | na | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | RETURN 1 as test 健康检查 ping, 无业务数据; 备忘录同样点名要求 @allow_cross_vault, 现场无装饰器 (仅声明缺位, 无泄漏风险)。 |
| `api/v1/endpoints/kg_health.py:45` | `kg_health_check` | call | read | (all nodes) | absent | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | MATCH (n) RETURN count(n) 全库节点计数 — 系统级 KG 健康指标, 备忘录归为 CROSS-VAULT BY DESIGN 但要求 @allow_cross_vault, endpoint 函数无装饰器, 仅靠 docstring 'Story 1.6 AC #3' 侧证意图。 |
| `api/v1/endpoints/kg_health.py:49` | `kg_health_check` | call | read | (all relationships) | absent | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | MATCH ()-[r]->() RETURN count(r) 全库关系计数, 同上系统级健康指标, 装饰器缺位。 |
| `api/v1/endpoints/kg_health.py:55` | `kg_health_check` | call | read | (all orphan nodes) | absent | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | MATCH (n) WHERE NOT (n)--() RETURN n.name LIMIT 20 全库孤儿巡检 — 设计上跨 vault, 但会把所有 vault 的孤儿节点 name 混在同一健康响应里对外输出 (轻度跨 vault 名称暴露), 且装饰器缺位。 |
| `api/v1/system.py:57` | `_check_neo4j` | call | ping |  | na | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | RETURN 1 AS n 连通性 ping, 不触任何业务节点; cypher_helpers 备忘录归为 CROSS-VAULT BY DESIGN 并要求 @allow_cross_vault, 现场无装饰器 (风险为零, 仅声明缺位)。 |
| `clients/neo4j_client.py:450` | `_run_query_neo4j (nested _execute_with_retry, via public run_query)` | call | read+write | (caller-supplied query) | conditional | unknown | R1:conditional,R4:conditional,W1:conditional | **CONDITIONAL** | 通用执行代理: session.run(query, params) 直接跑调用方传入的任意 Cypher, 本层不注入 group_id 也不校验物理格式; cypher_helpers 备忘录标为 GENERIC WRAPPER out-of-scope, 隔离责任完全落在每个 callsite — 任何调用方漏传过滤即静默全库扫描。 |
| `core/subject_config.py:85` | `list_subjects_from_neo4j` | call | read | Subject | absent | na | R2:needs-decorator | **CROSS-VAULT-BY-DESIGN** | bootstrap 列出全部 :Subject 注册节点 (该标签无 group_id 属性), cypher_helpers 备忘录明确归为 CROSS-VAULT BY DESIGN 但要求补 @allow_cross_vault, 当前函数无装饰器 — 意图仅靠备忘录侧记, 现场未声明。 |
| `services/cross_subject_bridge.py:164` | `expand_search_subjects` | call | read | CanvasNode | filtered | yes | R1:ok,R4:ok,R5:ok | **COMPLIANT** | P0-SYNC-ISO R10 修复版: WHERE (n.group_id = $vault_group OR STARTS WITH $vault_prefix) 按 vault 根前缀过滤 (=与 prefix+'__' 并用防 vault__a 撞 vault__a2), 参数经 _physical_vault_scope→to_physical_group_id 物理化; group_id 空时兜底 ContextVar 仍产生 vault 过滤, 不退化全库扫描。 |
| `services/cross_subject_bridge.py:226` | `get_subject_tags_from_neo4j` | call | read | CanvasNode | filtered | yes | R1:ok,R4:ok,R5:ok | **COMPLIANT** | MATCH (n:CanvasNode {subjectId:$subject_id}) + vault_group/vault_prefix 双条件过滤, 物理化同 _physical_vault_scope; 修掉了旧版跨 vault 同名 subjectId tag 集互污问题。 |
| `services/group_id_migration_service.py:182` | `migrate_legacy_group_ids` | call | read | (all nodes with group_id) | absent | na | R2:ok(docstring) | **CROSS-VAULT-BY-DESIGN** | 迁移工具扫描: MATCH (n) WHERE n.group_id IS NOT NULL RETURN DISTINCT gid+count — 管理性全库扫描, dry_run=True 默认只读报告; docstring 声明充分 = 合规最低线; @allow_cross_vault 装饰器为推荐形态待补挂 (advisory, 非违规)。 |
| `services/group_id_migration_service.py:225` | `migrate_legacy_group_ids` | call | write | (all labels, by group_id) | filtered | yes | W4:ok(docstring),W3:ok,W5:ok | **CROSS-VAULT-BY-DESIGN** | 迁移写: MATCH (n) WHERE n.group_id=$old SET n.group_id=$new — 按旧 group_id 等值 scope 逐组改写, new 值经 to_physical_group_id 物理化且 vault__ 存量先跳过防二次绞碎; 仅 dry_run=False 才执行, docstring 声明充分 = W4 合规最低线; 装饰器为推荐形态待补挂 (advisory)。 |
| `services/schema_gate.py:76` | `CanvasSchemaGate.verify` | call | schema | (constraints metadata) | na | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | SHOW CONSTRAINTS schema 巡检 — 只读约束元数据核对 migrations/003 三条复合唯一约束是否在位, 不触业务节点; 模块 docstring 明确声明 fail-closed gate 意图 (P2-02), 无装饰器但属 R2 允许的注释声明形态。 |
| `services/sync_service.py:470` | `_upsert_node` | call | write | CanvasNode | filtered | yes | W1:ok,W3:ok,W5:ok | **COMPLIANT** | MERGE (n:CanvasNode {id:$entity_id, group_id:$group_id}) 复合身份键含 group_id; group_id 为必传参数, 由 endpoint 层 sync.py:120 to_physical_group_id 物理化后下传, 无静默 fallback |
| `services/sync_service.py:505` | `_delete_node` | call | delete | CanvasNode | filtered | yes | W2:ok,W3:ok | **COMPLIANT** | DETACH DELETE 的 MATCH 带 {id, group_id} 复合 scope, 跨 vault 同 id 节点不可误删 |
| `services/sync_service.py:560` | `_upsert_edge` | call | delete | CanvasNode, CANVAS_EDGE | filtered | yes | W2:ok,W3:ok | **COMPLIANT** | stale 边清理: 关系 pattern 本身带 {id, group_id}, 删除对象 group-scoped; 端点节点 os/ot 未加 group 过滤但仅用于端点比较不扩大删除范围, 风险可忽略 |
| `services/sync_service.py:578` | `_upsert_edge` | call | read+write | CanvasNode, CANVAS_EDGE | filtered | yes | R1:ok,W1:ok,W3:ok,W5:ok | **COMPLIANT** | OPTIONAL MATCH 端点均带 {id, group_id}, MERGE 边键含 group_id; 跨 vault 同 id 端点按设计返回 status='missing' 抛 SyncDependencyError, 禁止借他 vault 节点当端点 |
| `services/sync_service.py:618` | `_delete_edge` | call | delete | CANVAS_EDGE | filtered | yes | W2:ok,W3:ok | **COMPLIANT** | MATCH ()-[e:CANVAS_EDGE {id, group_id}]->() DELETE e, 关系匹配带复合 group scope; 匿名端点节点不影响删除范围 |
| `services/sync_service.py:639` | `_upsert_board` | call | write | CanvasBoard | filtered | yes | W1:ok,W3:ok,W5:ok | **COMPLIANT** | MERGE (b:CanvasBoard {id:$entity_id, group_id:$group_id}) 复合身份键含 group_id, 物理格式由 endpoint 边界统一转换 |
| `services/sync_service.py:663` | `_delete_board` | call | delete | CanvasBoard, CanvasNode | filtered | yes | W2:ok,W3:ok | **COMPLIANT** | 级联删除最高危路径: board 侧与 node 侧 MATCH 均带 group_id (docstring 明示 P0-SYNC-ISO 防跨 vault 整板误删), 复合 scope 完整 |
| `services/vault_identity_registry.py:124` | `VaultIdentityRegistry.assert_identity` | call | schema | VaultIdentity | na | na | R2:ok | **CROSS-VAULT-BY-DESIGN** | CREATE CONSTRAINT vault_identity_gid_unique IF NOT EXISTS — 注册表自身唯一约束 DDL, 纯 schema 操作不触业务数据; 模块 docstring 详细声明 meta 注册表意图 (P0-01 非单射防御), 无 @allow_cross_vault 但注释声明充分。 |
| `services/vault_identity_registry.py:126` | `VaultIdentityRegistry.assert_identity` | call | read+write | VaultIdentity | id-scoped | yes | W1:ok,W3:ok | **COMPLIANT** | _CLAIM_QUERY: MERGE (v:VaultIdentity {physical_gid:$physical_gid}) ON CREATE SET — 身份键即物理 group_id 本身且有唯一约束兜并发, 每次写只触一个 vault 的注册节点; physical_gid 按参数契约已是 vault__ 物理格式 (调用方 config.sanitize 链产出)。 |
| `utils/cypher_helpers.py:3` | `module docstring (cypher_helpers)` | docstring | na |  | na | na | na | **NON-QUERY** | 模块级政策 docstring: 声明 services/+clients/ 的裸 session.run/tx.run 必须走 cypher_with_group_filter 或标 @allow_cross_vault — 是契约文本本身, 非真调用。 |
| `utils/cypher_helpers.py:10` | `module docstring (cypher_helpers)` | docstring | na |  | na | na | na | **NON-QUERY** | 同一政策 docstring 的续行, 说明 lefthook pre-commit grep 门只是启发式 (抓 ~80% 裸 tx.run), 多行 Cypher 可能漏网 — 非真调用。 |
| `utils/cypher_helpers.py:125` | `cypher_with_group_filter (docstring)` | docstring | na |  | na | na | na | **NON-QUERY** | 函数 docstring 的 Returns 说明行 (params 供 tx.run 用); 同一 docstring 明确警示 T1 契约: 本函数只注 WHERE 不做物理化, 绑定值须调用方先过 to_physical_group_id — 非真调用。 |

## §5 `neo4j_client.py` 19 条 Cypher 语句逐条精分类

（语句级口径；行号为查询字符串所在区间。该文件为 Story 30.2 遗留的 Memory 系统客户端，是**无 group 防御的重灾区**。）

| # | 行号 | 方法 | op | 分类 | 判定 |
|---|---|---|---|---|---|
| 1 | L725-736 | `create_learning_relationship` | write | `MERGE (c:Concept {name})` 仅按 name 合并 + 后置 `SET c.group_id` → 跨 vault 同名概念冲撞、last-write-wins 劫持归属；`MERGE (u)-[r:LEARNED]->(c)` 的 r.group_id 同样被 clobber。W3 合规（L738 物理化） | **W1:violation**（写身份缺 group 复合键 ①） |
| 2 | L823-833 | `get_review_suggestions`（有 group 分支） | read | `WHERE r.next_review < datetime() AND c.group_id = $groupId`，L839 物理化；但 `r:LEARNED` 自身带 group_id 属性且未过滤 — 因 #1 的 clobber 缺陷，存量图上 r.group_id 可与 c.group_id 不同组，读回的 score/review_count 可能是他 vault 写入 | **CONDITIONAL**（R1:partial，Codex 整改 2026-08-27） |
| 3 | L842-852 | `get_review_suggestions`（无 group 分支） | read | group_id 不传即无 group 过滤（仅 user scope）— 静默退化分支 | **R4:violation**（无 group 读 ①） |
| 4 | L925-956 | `get_learning_history` | read | group 过滤仅在传参时拼接（`AND r.group_id = $groupId`）；物理化 + 输出 desanitize（L959-967）均合规 | CONDITIONAL（R4 风险；R5:ok） |
| 5 | L1071-1079 | `create_canvas_node_relationship` | write | `MERGE (c:Canvas {path})` / `MERGE (n:Node {id})` 全无 group_id | **W1:violation**（写身份 ②） |
| 6 | L1114-1122 | `create_edge_relationship` | write | Canvas/Node/CONNECTS_TO 三层 MERGE 全无 group_id | **W1:violation**（写身份 ③） |
| 7 | L1146-1150 | `delete_edge_relationship` | delete | `MATCH ()-[r:CONNECTS_TO {edge_id}]->() DELETE r` — 按属性全库删，edge_id 无全局唯一性保证 | **W2:violation**（无 scope 删除 ①） |
| 8 | L1180-1186 | `get_concept_score_history` | read | 按 Node id + Canvas path scope，无 group；node id 为 canvas 派生非 uuid 级全局唯一 | **R1:violation**（无 group 读 ②） |
| 9 | L1286-1300 | `record_score_history` | write | `MERGE (n:Node {id})` / `MERGE (c:Canvas {path})` + `CREATE (e:Episode)` 全无 group_id | **W1:violation**（写身份 ④） |
| 10 | L1376-1388 | `create_canvas_association` | write | `MERGE (:Canvas {path})` ×2 + ASSOCIATED_WITH 无 group_id | **W1:violation**（写身份 ⑤） |
| 11 | L1508-1524 | `get_canvas_associations`（path+type） | read | 仅按 Canvas path / association_type 过滤，无 group | **R1:violation**（无 group 读 ③） |
| 12 | L1532-1547 | `get_canvas_associations`（仅 path） | read | 同上 | **R1:violation**（无 group 读 ④） |
| 13 | L1550-1565 | `get_canvas_associations`（仅 type） | read | 按类型全库扫 | **R1:violation**（无 group 读 ⑤） |
| 14 | L1570-1584 | `get_canvas_associations`（无过滤） | read | 全库 ASSOCIATED_WITH 扫描（LIMIT 兜底） | **R1:violation**（无 group 读 ⑥） |
| 15 | L1638-1642 | `delete_canvas_association` | delete | 按 association_id 点删：该 ID 由调用方外部传入、无服务端生成点约束，uuid4 来源**不可证**，不满足 W2 窄例外；MATCH 又无 group 限定 | **W2:violation**（无 scope 删除 ②） |
| 16 | L1743-1747 | `update_canvas_association` | write | `MATCH …{association_id} SET …` 仅按 association_id 匹配 | W5:violation |
| 17 | L1841-1848 | `get_canvas_concepts` | read | 按 canvas path，UNION 两分支均无 group | **R1:violation**（无 group 读 ⑦） |
| 18 | L1911-1919 | `find_common_concepts` | read | 两 canvas path scope，无 group | **R1:violation**（无 group 读 ⑧） |
| 19 | L1967-1978 | `get_all_recent_episodes` | read | `MATCH (u:User)-[r:LEARNED]->(c:Concept)` 全库扫描（仅 LIMIT） | **R1:violation**（无 group 读 ⑨） |

**汇总（Codex round-1 复算修正 2026-08-27）**: 19 条 = **VIOLATION 17 / CONDITIONAL 2 / COMPLIANT 0**。
- 写身份缺 group 复合键（W1）**5 处**: #1/#5/#6/#9/#10
- 无 scope 删除（W2）**2 处**: #7/#15
- 无 group 读（R1/R4）**9 处**: #3/#8/#11/#12/#13/#14/#17/#18/#19（卡片勘探"6+ 处"实测为 9）
- 更新匹配无 group scope（W5）**1 处**: #16（round-1 汇总曾漏计，已补）
- CONDITIONAL **2 处**: #2（r alias 未过滤）/ #4（group 过滤依赖可选参数）
另: L446-450 通用执行代理归 §4 B 面（CONDITIONAL / GENERIC WRAPPER），不计入本表 19 条。`_run_query_json_fallback`（L477-505）为 JSON 模拟层非 Cypher，不计入。单例 `get_neo4j_client()` 默认连 `settings.neo4j_uri`（现网）。

## §6 scripts 40 处文件级粗分类

**深度声明: 本节为文件级粗分类，未逐条精判**（各文件 note 中重申）。

#### `backend/scripts/quarantine_test_pollution.py`（8 处）

- **用途**: 离线迁移工具 (MEM-FLYWHEEL 批次1'③): 把测试污染节点/边按内容关键词谓词 (TestConcept/UAT-2.5/m3-e2e/裸词'测试') 迁出到隔离组 quarantine__mem_cleanup (SET group_id + quarantined_from 可逆), 默认 dry-run, --execute 迁出, --restore 恢复
- **读写构成**: 3 read (dry-run 盘点) / 5 update (MATCH...SET group_id 迁移, 含 2 条 --restore 反向; 无 DELETE)
- **group 处理**: 谓词按内容关键词扫全库 (仅排除 n.group_id <> $q), 故意跨 vault 清污; 意图仅在 docstring 声明, 无 @allow_cross_vault 装饰器 (R2/W4:needs-decorator); group_id 绑定值全部为硬编码物理格式字面量 (quarantine__mem_cleanup / vault__canvas_vault__uat_2_5_x_test), 未过 to_physical_group_id() 但已是 vault__ 双下划线形态; --restore 按 quarantined_from 回写属可逆设计
- **跨 vault**: yes ｜ **风险**: medium
- **备注**: 文件级粗分类, 未逐条精判。风险点: --execute 对 live 库 (settings.NEO4J_URI, 默认 bolt://localhost:7687) 做跨全库内容关键词匹配的 SET group_id 写, 任何 vault 中 name/content 恰含 'm3-e2e'/'UAT-2.5' 等关键词的节点会被连带迁出 (无 uuid 精确定位); 缓解: dry-run 默认 + SET 非 DELETE + quarantined_from 可逆。粗判 verdict 倾向 CROSS-VAULT-BY-DESIGN (docstring 声明) 但缺显式装饰器标注

#### `backend/scripts/quarantine_graphiti_pollution.py`（7 处）

- **用途**: P1-05b 步骤3 隔离执行 (用户 2026-08-19 批准): 把当前 vault 主组内禁区 stem 命中的 RELATES_TO 边和无活边 Entity 节点 SET group_id 到隔离组 quarantine__p105b (裸 Cypher 绕 EntityEdge.save NPE), 默认 dry-run, --apply 真写, 后附四道验收门 (含生产 reader 冒烟)
- **读写构成**: 5 read (preview + n_stuck + 门1/门2/门4, 均 routing_='r') / 2 update (边隔离 SET + 节点隔离 SET; 无 DELETE)
- **group 处理**: 全部 7 条查询均带 group_id 等值/前缀过滤 (源组 $gid 或隔离组 $q); 源组经 sanitize_group_id_for_graphiti(build_vault_group_id(...)) 物理化 (等效 to_physical_group_id 链的 sanitize 段, 输入为 build_vault_group_id 产出的规范逻辑格式, 功能上满足 R5/W3); 写仅作用于当前 vault 主组 → 隔离组, 且叠加 source+node_id(stem) 双重收窄; 门2 的 STARTS WITH 前缀扫描是复刻生产 _expand_vault_subgroups 的验收检查
- **跨 vault**: no ｜ **风险**: low
- **备注**: 文件级粗分类, 未逐条精判。连接 live 库 (settings.NEO4J_URI 默认 bolt://localhost:7687), 但写在 --apply 之后且 scope 收窄到单 vault 主组 + 禁区 stem + source 白名单, 碰撞 stem 防御性排除, 有主组活边的节点不迁 (防跨组悬挂), 四门验收含真实读路径冒烟。粗判 verdict 倾向 COMPLIANT (物理化经 sanitize 而非字面 to_physical_group_id, 可在精判轮确认等价性)

#### `backend/scripts/census_graphiti_pollution.py`（5 处）

- **用途**: P1-05b 步骤2 只读盘点 (census): 统计 structured_writer 四通道边在各 group 的污染分布 (Q0 组分布 / Q1 禁区 stem 爆炸半径 / Q2 磁盘无法解释的补集 / Q3 禁区命名 Entity 节点), 无写模式, 隔离执行需用户过目报告后另行批准
- **读写构成**: 5 read (全部 MATCH/RETURN 计数聚合, 均 routing_='r'; 0 write)
- **group 处理**: Q0 故意不带 group 过滤 (跨全库摸清 group_id × source 分布, 这正是盘点目的); Q1/Q2/Q2b/Q3 均带 r.group_id = $gid 等值过滤, 但 $gid 迭代自 Q0 发现的全部组 → 整体是声明式跨 vault 审计; 意图在 docstring 显式声明 ('只读盘点/routing_=r/不输出正文'), 无装饰器; 对照组 gid 经 sanitize_group_id_for_graphiti(build_vault_group_id/DEFAULT_GROUP_ID) 物理化
- **跨 vault**: yes ｜ **风险**: low
- **备注**: 文件级粗分类, 未逐条精判。连接 live 库 (settings.NEO4J_URI 默认 bolt://localhost:7687) 但纯只读 + 只读路由 + 无 --apply 入口 (--dry-run 恒 True 仅语义显式), 不输出 fact 正文只出计数。粗判 verdict 倾向 CROSS-VAULT-BY-DESIGN (R2 docstring 声明充分, 缺 @allow_cross_vault 装饰器可在精判轮定夺是否要求补挂)

#### `backend/scripts/verify_targeted_exam_chain.py`（7 处）

- **用途**: GAP-D/GAP-E 端到端探针脚本: 验证「累积批注/节点增殖原因 → 检验白板针对性考察」读写主链 (Probe0 真实图谱普查 + Layer1 seed 读路径 + Layer2 真实写入 + Layer3 frontmatter 同步), probe 数据自清理
- **读写构成**: 2 detach-delete (cleanup) / 2 write (1 CREATE seed + 1 MERGE seed) / 2 read / 1 RETURN-1 ping
- **group 处理**: 无 group_id 过滤: cleanup 删除与 Layer2 读用 probe 前缀 (node_id STARTS WITH '__e2e_probe__') scope 而非 group; Probe0 普查故意全图跨 vault 读 (docstring 声明, 无 @allow_cross_vault 装饰器, R2:needs-decorator); seed CREATE 写 group_id='vault:__e2e_probe__:main' 逻辑格式未过 to_physical_group_id (W3 隐患); CanvasNode MERGE 身份键仅 {id} 无 group_id (W1 形式违规, 靠 probe 前缀避撞)
- **跨 vault**: yes ｜ **风险**: medium
- **备注**: 文件级粗分类, 未逐条精判。经 app.clients.neo4j_client.get_neo4j_client() 连 settings.NEO4J_URI (默认 bolt://localhost:7687, .env 实际指现网) — 会在真实图谱上执行 seed 写入和 DETACH DELETE 清理, 但删除严格限 probe 前缀且 finally 自清理; 有 JSON-fallback 检测 (未连真库即退出 2)

#### `backend/scripts/verify_graphiti_native_chain.py`（4 处）

- **用途**: Phase 5 Graphiti-native 主链端到端验证: 断言 structured_writer 写出 :Entity-RELATES_TO canonical 边、不再产出 :EpisodicNode{node_id} (Fix-D 已死)、reader 读回、belief 3 版本链 bitemporal 正确; probe 自清理
- **读写构成**: 2 detach-delete (cleanup) / 2 read (count 断言)
- **group 处理**: 直接 Cypher 4 处全部用 probe 前缀 (name/node_id STARTS WITH '__gn_probe__') scope, 无 group_id 过滤 — 跨 vault 前缀扫描, docstring 声明验证意图但无装饰器 (R2:needs-decorator); 业务写入走 structured_writer/belief_service 服务层 (不在本清单), gid=DEFAULT_GROUP_ID (config 归一化), 物理化取决于服务层实现
- **跨 vault**: yes ｜ **风险**: medium
- **备注**: 文件级粗分类, 未逐条精判。直连 graphiti_core Neo4jDriver(uri=settings.NEO4J_URI) = 现网库; DETACH DELETE 限 probe 前缀且 finally 自清理; belief 写入落在 DEFAULT_GROUP_ID 组内 (探针数据短暂进入真实 group, 靠 cleanup 的 Entity 前缀 DETACH 带走)

#### `backend/scripts/migrate_canvas_group_isolation.py`（2 处）

- **用途**: P0-SYNC-ISO-2026-08-17 迁移执行器 (migrations/003 自动化): CanvasNode/CanvasBoard/CANVAS_EDGE 的 NULL group_id census → 回填 (board→node 板继承→edge) → verify gate → 复合唯一约束替换 (先建后删)
- **读写构成**: 2 个执行漏斗: _fetch (承载 ~13 条只读 census/dup/歧义查询 + 3 条回填 MATCH...SET 更新), run_constraint_swap (3 CREATE CONSTRAINT + 2 DROP CONSTRAINT DDL)
- **group 处理**: 全图 WHERE group_id IS NULL 扫描 = 迁移工具设计本意的跨 vault 读写 (W4/R2: docstring 极充分声明, 无装饰器); default_gid 经 to_physical_group_id 物理化 (W3:ok); 回填 SET 仅命中 NULL 行幂等; 四重闸: dry-run 默认 / census blocker (重复+歧义即中止) / verify NULL 归零 gate / --apply 交互确认或 --force
- **跨 vault**: yes ｜ **风险**: medium
- **备注**: 文件级粗分类, 未逐条精判 (site_count=2 为 session.run 调用点, 实际承载 ~18 条 Cypher 常量)。连接 --uri 参数或 settings.NEO4J_URI 默认 — 可直指现网 7689/7691 生产库执行写迁移, 属 CROSS-VAULT-BY-DESIGN 管理工具; 防护闸完备但 DDL 约束替换不可逆

#### `scripts/test-a11-end-to-end.py`（6 处）

- **用途**: A11 kg_relevance 修复的用户可见端到端验证驱动: 在专用测试 Neo4j (7692) seed 5 主节点+8 filler+18 边, 验证 _get_kg_relevance 加权度公式与 select_target_node 选点顺序, Rich 报表输出
- **读写构成**: 1 detach-delete (clear canvas) / 2 merge-write (seed node + seed edge) / 3 read (schema count 断言)
- **group 处理**: 完全无 group_id: 6 处全部用 canvasId='a11-test-canvas' scope; MERGE (n:CanvasNode {id}) 身份键无 group_id (W1 形式违规, 复刻 SyncService 旧 schema 是脚本本意 — 验证的就是无 group 时代的 A11 修复); 无物理化 (无 group 可物理化)
- **跨 vault**: unclear ｜ **风险**: low
- **备注**: 文件级粗分类, 未逐条精判。硬编码 TEST_NEO4J_URI='bolt://localhost:7692' 专用测试容器 + import 前强制 os.environ 覆盖 + get_neo4j_client 单例 pin 到测试 client — 三重隔离不碰现网 7691; cross_vault 标 unclear 因目标库无 vault 概念 (单测试 canvas scope, 非跨 vault 扫描也非 group scope)

#### `scripts/health_check_epic12.py`（1 处）

- **用途**: Epic 12 健康检查脚本: 巡检 Neo4j/LanceDB/Graphiti/Agentic RAG/FSRS/LangSmith/Cohere/OpenAI 八项服务连通性与配置状态, 支持 --json/--verbose
- **读写构成**: 1 read (MATCH (n) RETURN count(n) 全图节点计数)
- **group 处理**: 无 group 过滤的全图 count — 典型系统健康巡检类跨 vault 读 (R2 场景: 意图明显但无 @allow_cross_vault 装饰器或注释声明, R2:needs-decorator); 无写入, 无物理化问题
- **跨 vault**: yes ｜ **风险**: low
- **备注**: 文件级粗分类, 未逐条精判。NEO4J_URI 环境变量默认 'bolt://localhost:7687' (非现网 7691, 需 env 显式指向才碰现网), 默认密码 fallback 'password123' 硬编码; 只读单查询, 泄漏面仅节点总数; 脚本属早期 Epic 12 遗留 (import src.agentic_rag 路径)


## §7 违规与条件性站点汇总（A/B 面）

### VIOLATION（6 处）

| 位置 | 契约 | 摘要 |
|---|---|---|
| `backend/app/services/mastery_store.py:312` | R1:violation,R5:ok | 违反 R1(部分): MATCH (c:Canvas)-[:CONTAINS_NODE]->(n:Node) 段仅按 c.path 匹配无 group 过滤——Canvas 节点在 neo4j_client.py:1072/1115/1288 仅按 {path} MERGE 本身无 group_id, 跨 vault 同名 canvas path 会把他 vault 的 node_ids 混入 collect(), 板级归属可被跨 vault 污染; 最终 EntityNode 段有 group 过滤故返回数据仍限本组。另有 L337 空结果时静默退化为组内全量 get_all_concepts(板级→组级放宽, docstring 已声明)。 |
| `backend/app/services/learning_context_service.py:105` | R1:violation, R3:n/a(name 非全局唯一) | fallback 查询完全无 group_id 过滤, 而函数明明持有 group_id 形参未绑定; n.name = $cid 跨 vault 同名概念可命中他 vault 的 EntityNode 并把其 name 注入上下文(mastery_concept_id 或许唯一但 OR name 分支破坏 R3 前提)。 |
| `backend/app/services/conversation_inheritance.py:124` | R1:violation | MATCH (n:EntityNode)-[r]-(neighbor:EntityNode) WHERE n.name = $node_id OR n.mastery_concept_id = $node_id 完全无 group_id 过滤; n.name 按名匹配非全局唯一 (R3 不适用), neighbor 侧也无 scope — 跨 vault 同名节点的邻居与关系会泄入对话继承上下文; 调用方 (line 67) 明明已解析 group_id 却未下传此查询 |
| `backend/app/clients/neo4j_edge_client.py:436` | R1:violation(R3 不适用) | 按 {id:$nodeId} 点查关联节点(可选 canvas_path 过滤)。canvas node id 属 R3 反例(可外部传入/缺失时仅取 UUID 前 8 位, 复制 canvas 撞 id, 唯一性不可证), 且 Node/CONNECTS_TO legacy 图无 group 属性可滤 — 与 §5 #11-14 同型, VIOLATION(R1; R3 不适用)。【Codex round-2 升级, round-3 清除矛盾旧句】 |
| `backend/app/services/fallback_sync_service.py:352` | W1:violation,W3:conditional,W5:violation | MERGE (c:Concept {name:$concept}) 仅按 name 合并 — 跨 vault 同名概念冲撞成同一节点, 后续 SET c.group_id=$groupId last-write-wins 劫持节点归属; r:LEARNED 更新 scope 同样无 group; 另 to_physical 有条件短路(group_id 为 None 时写 null group_id)。 |
| `backend/app/services/fallback_sync_service.py:458` | W1:violation,W3:conditional,W5:violation | 与 352 行同形: MERGE Concept 仅按 name, 跨 vault 同名冲撞 + SET c.group_id/r.group_id last-write-wins 覆盖; 额外 SET r.next_review 使 FSRS 复习状态也被跨 vault 串写; _build_group_id_from_canvas 可返回 None → groupId=null。 |

### CONDITIONAL（16 处：部分 alias 未过滤 / 可选参数静默退化 / legacy 直通等风险面）

| 位置 | 契约 | 摘要 |
|---|---|---|
| `backend/app/services/exam_service_ext.py:148` | W1:partial,W3:ok,W5:partial | 两端点 MATCH 均带 {id,group_id} 复合限定, 边属性 r.group_id 物理化写入; 空匹配 (跨 group 端点) 有显式检测降 edge_created=False, 不静默借端点。【Codex round-3 整改 2026-08-27】边 MERGE 身份键仅 {relation_type}, group_id 为后置 SET — 端点虽双双 group 锁定, 但同端点间已存在的错组/NULL 组存量边可被 MERGE 命中并覆写, 按'关系不跨组前提不可证'严格口径降 CONDITIONAL（写侧边键正例见 sync_service.py:578 的 {id, group_id} 复合边键） |
| `backend/app/api/v1/endpoints/profile.py:230` | R1:partial,R5:ok | 锚点 n.group_id 等值过滤 + to_physical_group_id 物理化; 两点残余风险: (1) 关联端 e:EpisodicNode 未单独过滤, 依赖关系不跨 group 的隐含前提; (2) group_id Query 默认 DEFAULT_GROUP_ID(deprecated cs188), 调用方漏传时静默落错 namespace(仍过滤, 非全库扫描)。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `backend/app/api/v1/endpoints/profile.py:299` | R1:partial,R5:ok | 同 tips 模式: n.group_id 等值过滤 + 物理化; 关联端 e 无标签且未过滤 group(依赖边不跨 group 前提), 默认 group_id 落 DEFAULT_GROUP_ID 同上。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `backend/app/api/v1/endpoints/profile.py:357` | R1:partial,R5:ok | 同 tips 模式: n.group_id 等值过滤 + 物理化; e 侧未单独过滤、默认 DEFAULT_GROUP_ID 两点残余风险同上。【Codex R1 整改 2026-08-27】锚点外 alias（e/r）未过滤 — 因 W1 写身份缺陷存量图上关系可跨组, '关系不跨 group' 前提不可证, 降 CONDITIONAL |
| `backend/app/services/recommendation_service.py:213` | R1:partial,R5:ok | 主 MATCH 带 {canvasId, group_id}; 内层 EXISTS 邻居未限组但只用于排除(跨vault脏边会让节点被保守排除, 不泄漏数据); 墓碑边 invalidated_at 已处理。【Codex round-2 整改 2026-08-27】EXISTS 子查询的匿名端点与边 e 未限组 — 跨 vault 脏边会让孤立节点被误判已连接而漏出推荐面, 降 CONDITIONAL |
| `backend/app/services/recommendation_service.py:246` | R1:partial,R5:ok | 端点 a/b 带 {canvasId, group_id} 且 shared.group_id = $group_id 显式过滤(带意图注释); 残留小缺口: *1..2 变长路径的中间过渡节点(非 shared)未查组, 依赖边不跨 vault 的数据假设。【Codex round-2 整改 2026-08-27】*1..2 变长路径的中间过渡节点与 es1/es2 边未查组('依赖边不跨 vault'假设在 W1 修复前不可证), 降 CONDITIONAL；NOT EXISTS 的 live:CANVAS_EDGE 排除边亦未过滤 group（round-3 补记） |
| `backend/app/services/recommendation_service.py:300` | R1:partial,R5:ok | 边 label 建议池查询两端点都带 group_id 过滤(注释明示跨 vault 边不得贡献建议), 墓碑边排除。【Codex round-2 整改 2026-08-27】两端点已过滤但边 e 自身 group_id 未过滤, 按 R1 严格口径降 CONDITIONAL |
| `backend/app/services/memory_service.py:1697` | R1:ok,R5:partial | STARTS WITH vault__x__ 前缀枚举白板级子组(punycode), 非等值但只能命中本 vault 前缀, 不跨 vault; 入参 _gid_phys 由调用方 sanitize_group_id_for_graphiti 物理化; 无标签全节点扫描仅返回 DISTINCT group_id, LIMIT 50 + 5min 缓存, 无业务数据泄漏。【Codex R5 整改 2026-08-27】绑定链为 sanitize_group_id_for_graphiti(非 to_physical_group_id), legacy cs188 无冒号输入原样直通不做 canonicalization(group_id_compat.py:64-87 vs 140-185), R5 降 partial → CONDITIONAL |
| `backend/app/services/memory_service.py:1845` | R1:conditional, R4:violation, R5:ok | WHERE ($group_ids IS NULL OR node.group_id IN $group_ids) — group_id 不传即静默全索引无过滤扫描, 正是 R4 禁止的可选参数分支; 且实际被踩中: learning_context_service._fetch_tips_and_errors 调 search_memories 未传 group_id。传参时物理化+影子组扩展+输出 desanitize 都正确。 |
| `backend/app/services/learning_context_service.py:387` | R1:conditional(NULL-group legacy 豁免), R5:ok | 两端点都过滤 (group_id = $gid OR group_id IS NULL), gid 经 to_physical_group_id 物理化; 但 OR IS NULL 分支让无主 legacy 节点同时出现在所有 vault 的邻居结果里(docstring 已声明向后兼容意图), 属过滤依赖分支的弱化；未过滤的关系 r 的 reason/label 字段被直接返回进上下文（round-3 补记） |
| `backend/app/services/question_generator.py:985` | R1:partial,R5:ok | 主节点与 neighbor 双侧均限定 group_id = vault_group 或 STARTS WITH vault_prefix (P0-SYNC-ISO R10), _physical_vault_scope 内经 to_physical_group_id 物理化; 另有 {id, canvasId} 复合绑定与墓碑边过滤, 节点侧过滤实现。【Codex round-2 整改 2026-08-27】r:CANVAS_EDGE\|RELATES_TO 关系自身带 group_id 属性未过滤 — 按 R1 严格口径降 CONDITIONAL（缓解: CanvasNode/CANVAS_EDGE 写侧已复合键化, 风险低于 Concept/LEARNED 面） |
| `backend/app/services/verification_service.py:2151` | R1:partial,R4:ok,R5:ok | by-name 串库查询 b/n/m 三 alias 全部限定 groupVault =/前缀 (P0-SYNC-ISO R10); _vault_scope_params 经 to_physical_group_id 物理化, group_id 缺省走 ContextVar 兜底且无上下文时收敛为不存在组返回空 (fail-closed, 非全库退化, R4 满足)。【Codex round-2 整改 2026-08-27】b/n/m 三节点 alias 全过滤但 r:CANVAS_EDGE 未过滤且返回 r.label — 节点 alias 覆盖仍是多 alias 手写 WHERE 的形态参考, 关系过滤缺口降 CONDITIONAL |
| `backend/app/clients/neo4j_edge_client.py:281` | R1:conditional,R4:silent-fallback,R5:ok | CONTAINS 兜底路径: group_id 为可选参数, 传入时 WHERE n.group_id=$groupId 且过 to_physical_group_id; 不传则无 group 过滤, 无标签 MATCH (n) 全图文本扫 = R4 静默跨 vault 退化。 |
| `backend/app/clients/neo4j_edge_client.py:370` | R1:conditional,R4:silent-fallback,R5:ok | fulltext 快路径: group_id 有传才加后置 WHERE 过滤(且已 to_physical); 不传则 queryNodes 结果跨全部 vault 返回, 与 281 行同一 CONDITIONAL 形态。 |
| `backend/app/services/graphiti_belief_service.py:132` | R1:ok,R5:partial | WHERE e.group_id=$group_id AND e.belief_key=$belief_key, group_id 为必传参数, routing_='r'; 但调用方物理化走 sanitize_group_id_for_graphiti 而非 to_physical_group_id — vault: 输入等价, 遗留裸值(如 cs188)不做 canonical 映射; 与本文件写侧同一 gid, 读写自洽。【Codex R5 整改 2026-08-27】note 原已标 R5:partial 但 verdict 误留 COMPLIANT, 与 memory_service:1697 同因(sanitize 不做 legacy canonicalization)统一降 CONDITIONAL |
| `backend/app/clients/neo4j_client.py:450` | R1:conditional,R4:conditional,W1:conditional | 通用执行代理: session.run(query, params) 直接跑调用方传入的任意 Cypher, 本层不注入 group_id 也不校验物理格式; cypher_helpers 备忘录标为 GENERIC WRAPPER out-of-scope, 隔离责任完全落在每个 callsite — 任何调用方漏传过滤即静默全库扫描。 |

### 交接链（Codex round-1 修订）

- **G2-3（写侧）**: `neo4j_client.py` 写身份 5 处（W1 #1/#5/#6/#9/#10）+ 无 scope 删除 2 处（W2 #7/#15）+ **更新无 scope 1 处（W5 #16，round-1 曾漏列）**；`fallback_sync_service.py:352/458` 与 #1 同形 W1 违规，宜同批修复。⚠️ 门测试两条 xfail(strict) **只覆盖 #1**（Concept/LEARNED 写身份）——G2-3 修其余 7 处时应按同模式扩展门测试（每类违规至少一条行为门），仅翻绿现有两条不构成全量验收。
- 读侧无 group 与 CONDITIONAL 16 处（A/B 面）收敛：后续卡（本卡铁律不改业务行为）。CONDITIONAL 16 处中 11 处为 Codex 三轮对抗复审从 COMPLIANT 降级（round-1 降 5 / round-2 降 5 / round-3 降 1，形态 = 部分 alias 未过滤 / 变长路径中间节点未查组 / sanitize 不做 legacy canonicalization / 边身份键缺 group），见 §9。
- `@allow_cross_vault` 装饰器补挂：**advisory backlog 非违规**（声明形态最低线 = 明确 docstring/注释，装饰器为推荐标准形态）——表内 `needs-decorator` 标注按此语义解读。

## §8 质量对账记录

- **覆盖对账**: 分类 99 条 vs grep 清单 99 条 — 逐 (file,line) 匹配，缺失 0 / 多余 0 / 重复 0。
- **人工抽查 6 处**（主循环读原代码复核）: `mastery_store.py:312`（R1 部分违规 ✓ Canvas/Node alias 未过滤）、`learning_context_service.py:105`（R1 违规 ✓ 持有 group_id 形参未绑定）、`conversation_inheritance.py:124`（R1 违规 ✓）、`fallback_sync_service.py:352`（W1 违规 ✓ MERGE Concept 仅按 name）、`memory_service.py:1845`（CONDITIONAL ✓ `$group_ids IS NULL OR` 分支）、`exam_service_ext.py:99`（COMPLIANT ✓ `MERGE (n:CanvasNode {id, group_id})` 复合键）。6/6 与分类一致。
- **helper 局限实证**: 7692 真库 EXPLAIN 四例（read/delete/set 注入 VALID；merge-lead 注入 INVALID `SyntaxError: Invalid input 'WHERE'`）。

## §9 Codex round-1 审查整改记录（2026-08-27）

Codex round-1 裁定 FAIL（1 BLOCKER / 2 HIGH / 3 MEDIUM / 2 LOW，原文存档 `codex-review-CARD-G2-1.md`）。逐条整改：

| # | 级别 | 指控 | 核实 | 整改 |
|---|---|---|---|---|
| 1 | BLOCKER | 部分 alias 未过滤仍判 COMPLIANT = false-green（profile ×3、§5 #2 等） | **属实**（亲证 profile.py:214-217 e/r 未过滤；且 W1 clobber 使"关系不跨组"前提不可证） | 5 处 A 面站点 COMPLIANT→CONDITIONAL（profile:230/299/357、memory_service:1697、graphiti_belief_service:132）；§5 #2 R1:ok→CONDITIONAL；R1 规则补"部分 alias 过滤 = CONDITIONAL 非 COMPLIANT"条款；判定分布已重算 |
| 2 | HIGH | R3/W2/W5 "全局唯一 ID"口径自相矛盾（edge_id 可退化端点拼接、canvas node id 外部传入/8 位截断、association_id 双标） | **属实**（neo4j_edge_client.py:165-168、canvas_service.py:792-794 证据成立） | R3 收紧为"服务端 uuid4 级生成 + 来源可证"，剔除 edge_id/canvas node id 示例并列为反例；W2/W5 改为两级制（默认 group scope；uuid 点删/点更为窄例外需来源证明），#15/#16 违规判定在新口径下自洽成立 |
| 3 | HIGH | §5 汇总算术错误（漏 #16 W5、把 §4 CONDITIONAL 通用代理算成 COMPLIANT）+ G2-3 交接漏 #16、xfail 只覆盖 #1 | **属实** | §5 汇总重算为 17 violation / 2 conditional / 0 compliant；交接链补 #16 + 明示 xfail 仅覆盖 #1、G2-3 需扩展门测试 |
| 4 | MEDIUM | xfail 可能因错误原因（连接异常/写入失败）被接受为 XFAIL | **属实** | 两条 xfail 加 `raises=AssertionError` 收窄 + 前置条件改 `pytest.fail()`（非 AssertionError 路径不再计 xfail） |
| 5 | MEDIUM | memory_service:1697 R5 false-clean（sanitize 不做 legacy canonicalization，cs188 直通） | **属实**（亲证 group_id_compat.py:64-87 vs 140-185） | 该行及同因 graphiti_belief_service:132 降 CONDITIONAL（R5:partial） |
| 6 | MEDIUM | 跨 vault 声明规则不可一致复算（装饰器 vs docstring 双标） | **属实** | R2/W4 统一口径：docstring/注释 = 合规最低线，装饰器 = 推荐标准形态（advisory backlog）；表内 `needs-decorator` 语义按此解读（见 §7） |
| 7 | LOW | fallback_sync_service:352/458 `physical=yes` 与 `W3:conditional` 自相矛盾 | **属实** | 两行物理化列改 conditional（group_id 为空时原样传递） |
| 8 | LOW | 读契约"见审计 §5"应为 §2 | **属实** | 已改 |

round-1 整改后判定分布（A/B 面 99 处）: COMPLIANT 61 / CROSS-VAULT 16 / CONDITIONAL 10 / NON-QUERY 7 / VIOLATION 5。

### Codex round-2 复审整改（2026-08-27，存档 `codex-review-CARD-G2-1-round2.md`：4 PASS / 4 FAIL）

| # | 级别 | 指控 | 核实 | 整改 |
|---|---|---|---|---|
| R2-1 | BLOCKER | 又 5 处同型 partial-alias false-green（question_generator:985、recommendation:213/246/300、verification:2151） | **属实**（逐处亲证：r/边/变长路径中间节点/EXISTS 匿名端点未过滤） | 5 处 COMPLIANT→CONDITIONAL；R1 正例更换为 `targeting_material_service.py:163`（n/e/m 三侧严格等值过滤——真正的全覆盖形态） |
| R2-2 | BLOCKER | `neo4j_edge_client.py:436` 的 canvas node id 点查判 R3:ok 与新 R3 反例直接冲突 | **属实**（同一行 note 已承认复制 canvas 撞 id） | 升 **VIOLATION**（R1，与 §5 #11-14 legacy 无 group 图读同型口径一致） |
| R2-3 | MEDIUM | memory_service:1697 / belief:132 物理化列 `no` 与"规范输入会被 sanitize 物理化"说明矛盾 | 属实 | 两行物理化列改 `conditional (sanitize 不做 legacy canonicalization)` |
| R2-4 | MEDIUM | migration 行仍写 `needs-decorator` / "W4 要求装饰器"，与 R2/W4 新口径（docstring=最低线）不一致 | 属实 | `group_id_migration_service:182/225` 契约改 `R2:ok(docstring)` / `W4:ok(docstring)`，note 改 advisory 措辞；其余 `needs-decorator` 行按 §7 图例解读（意图仅侧证、声明确实偏弱的健康巡检类） |
| R2-5 | LOW | §7 CONDITIONAL 标题"R4 静默退化风险面"以偏概全 | 属实 | 标题改为"部分 alias 未过滤 / 可选参数静默退化 / legacy 直通等风险面" |
| R2-6 | LOW | §5 #15 说明残留"uuid 勉强够线"与新 W2 论证冲突 | 属实 | #15 说明改写为"外部传入、uuid4 来源不可证，不满足 W2 窄例外" |

round-2 整改后判定分布（A/B 面 99 处）: COMPLIANT 55 / CROSS-VAULT 16 / CONDITIONAL 15 / NON-QUERY 7 / VIOLATION 6。

### Codex round-3 终审整改（2026-08-27，存档 `codex-review-CARD-G2-1-round3.md`）

round-3 对指定整改项全数 PASS，扫尾再出 1 BLOCKER + 1 MEDIUM + 4 LOW，逐条整改：

| # | 级别 | 指控 | 核实 | 整改 |
|---|---|---|---|---|
| R3-1 | BLOCKER | `exam_service_ext.py:148` 边 MERGE 身份键仅 `{relation_type}`、group 后置 SET，仍判 COMPLIANT | **属实**（亲证 L138-143：端点双锁 group 但存量错组/NULL 边可被命中覆写） | 降 **CONDITIONAL**（W1:partial/W5:partial）；"全覆盖正例"句同步修正 |
| R3-2 | MEDIUM | 交接链仍写 CONDITIONAL 10，与实际不符 | 属实 | 改为 16 并注明三轮降级构成 |
| R3-3 | LOW | edge_client:436 note 残留"R3 免 group 过滤"旧句自相矛盾 | 属实 | note 整句重写，矛盾清除 |
| R3-4 | LOW | question_generator:985 note 残留"模范实现"旧誉 | 属实 | 改"节点侧过滤实现" |
| R3-5 | LOW | recommendation:246 note 漏记 NOT EXISTS live 边未过滤 | 属实 | 已补记 |
| R3-6 | LOW | learning_context:387 note 漏记未过滤 r 的 reason/label 被返回 | 属实 | 已补记 |

**round-3 整改后最终判定分布（A/B 面 99 处）: COMPLIANT 54 / CROSS-VAULT-BY-DESIGN 16 / CONDITIONAL 16 / NON-QUERY 7 / VIOLATION 6。**
读侧全覆盖正例（节点与关系 alias 全过滤）**仅 1 处**: `targeting_material_service.py:163`。写侧复合键正例: `sync_service.py:578`（边键 `{id, group_id}`）、`exam_service_ext.py:99`（节点键 `{id, group_id}`）、`mastery_store.py:95`（`{group_id, mastery_concept_id}`）。终审确认见 `codex-review-CARD-G2-1-round4.md`。
