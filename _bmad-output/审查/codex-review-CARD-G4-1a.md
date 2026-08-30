# 审查裁定

**需整改（不可合并）。**

当前改动确实封住了主要 HTTP → MemoryService → Neo4j 的 `group_id=None` 路径，35 条真库门和 37 条新增单元门也通过；但仍有 3 个可构造的跨 vault 泄漏面，以及多处 fail-closed 静默失效，未达到 R1–R5 的可合并标准。

## BLOCKER

### B-1 — inheritance 对 NULL 关系放行，违反 R1 且可泄漏关系语义

- **问题描述**：节点虽然严格锚定，关系 `r` 却允许 `group_id IS NULL`。契约已明确禁止依赖“两端节点同组，所以边不可能跨库”的隐含前提。

- **证据**：

  [cypher-read-contract.md:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/.claude/rules/cypher-read-contract.md:25) 要求每个关系 alias 逐一严格过滤，部分过滤只能判 CONDITIONAL；[conversation_inheritance.py:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/conversation_inheritance.py:143) 实际为：

  ```python
  AND {read_group_filter("n")}
  AND {read_group_filter("neighbor")}
  AND {read_group_filter("r", allow_null=True)}
  ```

  同一查询返回 `r.label`、`r.reason`。Gate fixture 的边全部显式带与端点相同的 group：[test_cypher_contract_gate.py:1003](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:1003)。

- **为什么是问题**：历史 W1 clobber 状态可以是：两个节点现归 A，但曾在 B 上下文生成的关系仍为 NULL group，且 `label/reason` 含 B 的语义。A 查询时两端通过，NULL 边也通过，B 的关系内容进入 A 对话。端点当前归属不能证明边内容来源。

- **建议修法**：改为严格 `read_group_filter("r")`。需要保留旧 NULL 边时，应先迁移、隔离或量化存量，不能运行时对所有 vault 放行。补 NULL 边和单 alias 异组真库负门。

### B-2 — client 的无 group 全库查询仍保留，R4 漏洞原语没有封死

- **问题描述**：`get_review_suggestions(None)` 仍在记录 error 后执行无过滤 Cypher；`get_learning_history(None)` 同型。

- **证据**：[neo4j_client.py:848](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/clients/neo4j_client.py:848) 仍声明 `group_id: Optional[str] = None`；[neo4j_client.py:906](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/clients/neo4j_client.py:906) 的 else 分支执行：

  ```cypher
  MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept)
  WHERE r.next_review < datetime()
  ```

  没有 `c/r.group_id`。现有单测甚至直接执行该分支：[test_neo4j_field_consistency.py:154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/unit/test_neo4j_field_consistency.py:154)。

- **为什么是问题**：全仓 grep 证明作者“唯一现有生产调用方是 MemoryService，且该调用方已传 group”这一点**属实**；当前注册 HTTP 路径不会走 None。但公共 singleton/client 仍可被 CLI、后台任务或新增 service 直接调用，立即恢复同一 user 的全 vault 扫描。这与 R4 点名禁止该分支直接冲突。

- **建议修法**：无需修改公开签名。保留 Optional 参数兼容，但方法入口统一 `read_scope_params(group_id, ...)`，删除无过滤分支；解析失败抛错。作者所称“删除分支必然导致签名半改”**不属实**。

### B-3 — `_fetch_tips_and_errors` 并未全调用链带 vault，真实 endpoint 仍会串库

- **问题描述**：本卡只更新了 `get_node_context` 调用方；`exam_quick` 接收强制 `vault_id`，却完全不解析、不下传。frontmatter 来源也无视传入 group。

- **证据**：

  - [exam_quick.py:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/api/v1/endpoints/exam_quick.py:62) 请求强制带 `vault_id`。
  - [exam_quick.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/api/v1/endpoints/exam_quick.py:98) 调用 `_fetch_tips_and_errors(req.node_id)`。
  - [learning_context_service.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/learning_context_service.py:151) 在 group 为 None 时由 MemoryService 推导进程 active vault。
  - [learning_context_service.py:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/learning_context_service.py:219) 的第三来源固定从 `settings.CANVAS_BASE_PATH` 读取。
  - 随后结果却被标记为请求中的 vault：[exam_quick.py:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/api/v1/endpoints/exam_quick.py:127)。

- **为什么是问题**：进程 active=A，请求提交 `vault_id=B`，且 A/B 有相同 `node_id`。endpoint 没有 409 一致性门，实际读取 A 的 Memory/frontmatter，却把问题记录标成 B。Canvas node ID 并非全局唯一，不能用 R3 豁免。

- **建议修法**：在 endpoint 的 try 外调用统一 vault resolver，把解析结果传给 `_fetch_tips_and_errors`；frontmatter 路径也必须由相同 resolved vault 决定。补 A/B 同 node ID 的 endpoint 负门。

## HIGH

### H-1 — `vault:default` 仍在真实配置和生产 scheduler 路径出现

- **问题描述**：作者声称“配置坏则抛错，不回落 DEFAULT_GROUP_ID”不成立。

- **证据**：

  [config.py:765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/config.py:765) 最终调用 `sanitize_vault_id(ACTIVE_VAULT)`；[config.py:1037](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/config.py:1037) 将空值/非法值变成 `"default"`。`require_read_group` 只验证非空，因此实测真实 `Settings(ACTIVE_VAULT="")` 得到：

  ```text
  require_read_group(...) == 'vault:default'
  ```

  新测试 [test_vault_scope_read_g41a.py:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/unit/test_vault_scope_read_g41a.py:76) 直接 monkeypatch getter 返回空串，绕过了真实 sanitizer。

  此外 [archive_scheduler.py:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/archive_scheduler.py:163) 对默认 truthy ContextVar `"general"` 执行 `canonical_group_id("general")`，稳定得到 `vault:default`；该 scheduler 在 [main.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/main.py:193) 每 24h 真实启动。

- **为什么是问题**：配置故障可能读污染桶或假空；scheduler 会长期认为没有 active conversations，或者处理污染桶中的错误节点。其 warning else 因 `"general"` 恒 truthy 而是死分支。

- **建议修法**：派生结果中的 `vault:default` 必须视为 unresolved；scheduler 删除本地解析，统一使用 `require_read_group/current_group_id`。测试必须构造真实 `Settings`，不能绕开 sanitizer。

### H-2 — score-history 复用写 resolver，正常后台读错到 default 子组

- **问题描述**：`get_concept_score_history` 在 `group_id=None`、无 ContextVar 时不抛错，而是读 `vault__default__<canvas>`。

- **证据**：[neo4j_client.py:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/clients/neo4j_client.py:106) 的写侧 resolver 在 canvas 存在时执行：

  ```python
  resolved = build_vault_group_id("default", subject_id=subject)
  ```

  新读路径在 [neo4j_client.py:1342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/clients/neo4j_client.py:1342) 复用它。独立实测：

  ```text
  ContextVar='general'
  _resolve_physical_group_id(None, 'board.canvas')
  -> 'vault__default__board'
  ```

  Gate [test_cypher_contract_gate.py:980](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:980) 只测试显式 `"   "`，没有测试生产默认 `None`。

- **为什么是问题**：后台/CLI 查询成功但零命中，上游 [memory_service.py:977](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/memory_service.py:977) 会把它标成正常 `empty` 并缓存，而非 `unavailable`，正是静默断读。

- **建议修法**：读方法直接调用 `read_scope_params(group_id, ...)`；canvas 只作查询条件，不参与 default-vault 推导。补无 ContextVar 的真实 client/service 门。

### H-3 — `VaultScopeUnresolved` 会被点名服务吞成空业务结果

- **问题描述**：异常继承 `RuntimeError`，恰好落入两个服务的“依赖失败降级”捕获范围。

- **证据**：

  - [vault_scope.py:359](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/core/vault_scope.py:359)：`class VaultScopeUnresolved(RuntimeError)`。
  - [conversation_inheritance.py:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/conversation_inheritance.py:162)：捕获 `RuntimeError` 后返回 `[]`。
  - [learning_context_service.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/learning_context_service.py:186)：同样吞掉后继续其他来源。

  动态注入作用域失败分别得到 `[]` 和 `([], [])`。

- **为什么是问题**：配置错误被呈现为“没有邻居/没有 tips”。`exam_quick` 又在 [exam_quick.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/api/v1/endpoints/exam_quick.py:100) 做第二层 `except Exception → tips=[]`，静默断读生产可达。

- **建议修法**：在宽捕获前显式 `except VaultScopeUnresolved: raise`，由 API 边界映射为明确配置/服务错误。MemoryService 三个公共入口的解析位于宽 try 外，这部分是 PASS。

### H-4 — Gate 6 没有证明 R1 “每个 alias 都过滤”

- **问题描述**：fixture 将所有 alias 都放在同一 group，任一 alias 过滤丢失仍会被其他 alias 拦住。

- **证据**：

  - review/history seed 同时给 `c/r` 同一个 gid：[test_cypher_contract_gate.py:827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:827)。
  - score 五 alias 通过同一生产写组构造：[test_cypher_contract_gate.py:955](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:955)。
  - inheritance 三 alias 同组：[test_cypher_contract_gate.py:1003](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:1003)。

  进程内负控把 `read_group_filter(alias="r")` 单独变为恒真后，Gate 6 仍为 **9/9 passed**；把 `allow_null=True` 改成严格也不会红。

- **为什么是问题**：删除 `r` 过滤或错误放行 NULL 都不会触发门。所谓“全局恒真/全局等值能红”只能证明整体方向，不能证明每个 alias 的 R1 合规。

- **建议修法**：为每个 alias 构造单独异组记录：`c=A/r=B`、`c=B/r=A`；score 对 `n/c/cn/r/e` 各做一次异组；inheritance 增加 NULL/异组关系与异组 neighbor。逐 alias 变异必须分别杀门。

## MEDIUM

### M-1 — canvas 子组隔离只测 helper，没有经过生产方法

- **证据**：[test_cypher_contract_gate.py:887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:887) 自行拼 Cypher 验证 board_x/board_y；生产 `get_review_suggestions/get_learning_history` 只以 vault 根组调用：[test_cypher_contract_gate.py:912](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:912)。

- **失败场景**：生产方法若把 `vault:A:board_x` 错误提升成 `vault:A`，helper 门和根组生产门仍绿，board_x 将看见父组及 board_y。

- **建议修法**：直接用两个生产方法传 canvas scope，断言只见 board_x 及其 semantic，不见 root、board_y、B、AB。

### M-2 — Graphiti “全部子组可见”被无序 `LIMIT 50` 截断

- **证据**：[memory_service.py:1965](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/memory_service.py:1965)：

  ```cypher
  MATCH (n)
  WHERE n.group_id STARTS WITH $prefix
  RETURN DISTINCT n.group_id AS gid
  LIMIT 50
  ```

- **失败场景**：一个 vault 超过 50 个白板/semantic/punycode 子组，第 51 个可能随机不进入 Graphiti `group_ids`，根组搜索静默漏召回，与 Cypher/内存前缀语义不等价。

- **建议修法**：分页枚举全部 distinct group，或让 Graphiti 原生支持 prefix；若必须限额，应确定性排序、返回 degraded 状态并增加 >50 组门。

### M-3 — 测试改动总体合理，但验收单“零新增失败”不成立

- **问题描述**：作者关于 fixture 的两个主要论据属实，但处置不完整。

- **证据与判断**：

  - `test_no_subject_means_no_group_id` 反转为 active vault scope：[test_story_31a2_ac4_pagination.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/unit/test_story_31a2_ac4_pagination.py:147)，这是合理 R4 变更。
  - 论据 (i) **属实**：batch/temporal 原本未给内存 episode 落 group；当前只给内存记录补字段，Neo4j payload 未改变。
  - 论据 (ii) **属实**：基线 sibling 用例确因无归属 episode 被作用域过滤而红。
  - 但当前 sibling fixture 给数学、物理两条都填 vault 根组：[test_story_31a2_ac4_pagination.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/unit/test_story_31a2_ac4_pagination.py:240)，subject=数学的子组作用域不能反向看到父组；定向执行仍 `assert 0 == 1`。
  - 另有真正新增红：[test_neo4j_field_consistency.py:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/unit/test_neo4j_field_consistency.py:171) 仍断言旧 `$groupId`。实跑为 **1 failed, 6 passed**；基线代码确实包含该旧片段，所以验收单的“零新增失败”不成立。

- **建议修法**：subject fixture 分别写入数学/物理子组；field consistency 更新为断言 `c/r`、`$group_id/$group_prefix` 及 `__` 定界符。重跑全部受影响文件，不要只依赖挑选清单。

### M-4 — 显式畸形 group 仍会被当成有效作用域

- **证据**：[vault_scope.py:395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/core/vault_scope.py:395) 只检查 canonical 结果非空；而 `canonical_group_id("vault:")` 原样返回。实际：

  ```text
  read_scope_params("vault:")  -> group_id='vault__'
  read_scope_params("vault__") -> group_id='vault__'
  ```

- **为什么是问题**：不会全库扫描，但会把非法配置伪装成正常空结果。

- **建议修法**：对逻辑/物理格式做段级验证，拒绝空段、`vault__` 和非授权的 `vault:default`。

## LOW

### L-1 — STARTS WITH 暂无实测回归，但缺规模与索引保障

7691 的只读 `EXPLAIN` 显示 review 查询先按 User expand LEARNED，再对 `c/r.group_id` 做 equality/`STARTS WITH` 后置过滤；相关 Concept/LEARNED/Node/Canvas 等 group 属性缺少适用索引。旧等值过滤同样是 post-expand，因此目前不能证明本卡造成实际回归，且现网仅一条 Concept/LEARNED，成本不可代表规模。

建议补生产规模 `PROFILE`，必要时增加 range index 或独立精确 `vault_id` 分区字段。性能不是本次不可合并的主因。

### L-2 — LearningMemoryClient secondary 实际是死 fallback

[learning_context_service.py:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/services/learning_context_service.py:194) 未传必填 `query`；真实签名见 [neo4j_edge_client.py:864](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/app/clients/neo4j_edge_client.py:864)。它会固定 TypeError，再被 211 行吞掉。此处当前不能作为跨库返回的证据，但确实是静默失效的 secondary。

## 已确认通过的部分

- 真 Neo4j 7692：**35 passed**；其中 Gate 6 为 **9 passed**。新增两单元文件：**37 passed**。
- Gate fixture 不会空库假绿：`g41a_seed` 依赖 function-scoped `gate_client`，清库后种数并自证 8 个 Concept：[test_cypher_contract_gate.py:816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend/tests/integration/test_cypher_contract_gate.py:816)。
- vault 根组的生产 review/history 门确实断言 root、canvas、semantic、punycode 子组召回；score 和 inheritance 也走真实生产查询。
- `group_prefix` 带 `__`，helper 层的兄弟/父组/近似前缀隔离正确。
- 合法物理输入与 punycode 往返精确无漂移。
- scoped Cypher alias 核对：review `c/r` PASS；history `c/r` PASS；score `n/c/cn/r/e` PASS；fulltext `node` PASS；inheritance `r` FAIL。
- 写侧范围 PASS：batch/temporal 只修改内存 episode；Neo4j payload/写身份未变。
- “唯一现有生产调用方”及测试论据 (i)(ii) 属实；但它们不能抵消上述规范违规。

作者的变异方向结论“等值会杀保召回、恒真会杀隔离”属实；精确数字不属实/不可复现。当前进程内变异下，Gate 6 两种全局变异均为 **6 failed / 3 passed**；逐 alias `r` 恒真却为 **9 passed**。仓库没有变异脚本、日志或 byte-restore receipt，因此验收单 [111–118 行](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/_bmad-output/审查/CARD-G4-1a-验收单.md:111>) 的精确计数及“逐字节恢复”只能判不可信/不可验证。

**最终裁定：需整改，不可合并。** 审查过程中未修改工作区文件，最终 `git status` 与起始改动清单一致。

