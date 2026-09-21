## 审查边界与绑定

- HEAD = `4f6d17ca59e734dfc757a3f9e293557121fb930d`，父提交 = `d0e42bc47c36b0aebb6d4c5cf6a76a3c3effb7be`，ancestry 已用只读 git 核验。
- `d0e42bc4..4f6d17ca` 只改 `backend/tests/integration/test_cypher_contract_gate.py`，`+150/-9`；`-w` 与非 `-w` numstat 相同，未见隐藏语义面。
- 未改文件、未连接 Neo4j、未访问网络、未运行 pytest/ruff。以下结论来自源码/只读 git/diff 静态复算。

## r2 三条 LOW 的闭合判定

| r2 项 | 判定 | 依据 |
|---|---|---|
| LOW-1：零写措辞与覆盖面 | **部分闭合** | 措辞失实已修：`backend/tests/integration/test_cypher_contract_gate.py:651-657` 明确只断言 Concept 与“按 record_id 的 Episode”，并登记 User/Node/Canvas/边及属性改写盲区；`:629-648` 的 Node/Canvas 前缀 count delta 能抓新增 Node/Canvas。当前生产拒写路径确在图写前返回：`backend/app/services/fallback_sync_service.py:912-920`。但随机 `id` 且无 `record_id` 的 Episode、User-only、边-only、既有 Node/Canvas 属性改写仍可全绿；若验收口径是“全域零写”，仍未完全闭合。 |
| LOW-2：固定 `unscoped_rid` 孤儿粘滞假红 | **真闭合** | 新清理 `backend/tests/integration/test_cypher_contract_gate.py:109-114` 直接按 `e.record_id STARTS WITH 'g21gate_'` `DETACH DELETE`。r2 假想孤儿即使 `group_id='vault__default__...'`、无 SCORED 边、group 非 null，也会被该查询删除。该清理在 function fixture setup/teardown 都执行：`:154-161`，模块同步 driver 也执行：`:124-131`。当前 repo 其它真库门使用 `t6bgate` / `p2cgate` 前缀，未发现顺序运行下的同前缀 `record_id` 碰撞。 |
| LOW-3：来源优先级矩阵 | **指定两格闭合，完整矩阵部分闭合** | `group_id` vs `vault_id` 冲突已由 `backend/tests/integration/test_cypher_contract_gate.py:670-706` 锁住；env 正向分支由 `:719-767` 锁住。断言口径与生产同源：resolver 为 `backend/app/services/fallback_sync_service.py:627-644`，Concept 物理化在 `:926-932`，Episode/Node/Canvas 走 `backend/app/clients/neo4j_client.py:1865-1868` 与 `:1896-1906`。但缺 `vault_id` vs env、以及 group/env/vault 三源同冲突的判据；详见 LOW-2。 |

## 两条新矩阵用例与清理复算

### 断言是否同源

- conflict 用例期望 `GID_A`：
  - `GID_A` 由生产同一物理化入口 `to_physical_group_id()` 得到：`backend/tests/integration/test_cypher_contract_gate.py:90-93`。
  - 生产 resolver 对非空 entry `group_id` 直接短路：`backend/app/services/fallback_sync_service.py:627-630`。
  - scoring Concept 使用 `physical_group = to_physical_group_id(group_id)`：`:926-932`。
  - Episode/Node/Canvas 再经 `record_score_history_by_record_id()` 的 `_resolve_physical_group_id()`，最终同样落到 `to_physical_group_id()`：`backend/app/clients/neo4j_client.py:96-116`、`:1865-1868`、`:1896-1906`。
  - 因此不是猜字符串。

- env 用例期望组在测试内现算：
  - `backend/tests/integration/test_cypher_contract_gate.py:748` 调 `build_vault_group_id(env_vault, canvas_path=entry["canvas_name"])` + `to_physical_group_id()`。
  - 生产 resolver 正是同一 builder 与 canvas 参数：`backend/app/services/fallback_sync_service.py:630-644`。
  - Concept 与 Episode 两条物理化链如上，覆盖了两个独立转换入口。
  - `ContextVar` 被设成 A 作负控，且 `finally reset`：测试 `:750-754`；能区分 env 与 active vault。

### 自清理是否删净

当前成功路径会写：

- User / Concept / LEARNED：`backend/app/services/fallback_sync_service.py:977-985`。
- Node / Canvas / CONTAINS_NODE / Episode / SCORED：`backend/app/clients/neo4j_client.py:1896-1906`。

两条新用例的自清理顺序为 Episode → Concept → Node → Canvas，且全是 `DETACH DELETE`：

- conflict：`backend/tests/integration/test_cypher_contract_gate.py:708-716`。
- env：`:769-776`。

因此：

- SCORED 边随 Episode/Node `DETACH DELETE` 删除。
- LEARNED 边随 Concept `DETACH DELETE` 删除。
- CONTAINS_NODE 随 Node/Canvas `DETACH DELETE` 删除。
- 四类节点均按本用例唯一键删除。

如果断言在自清理前失败，function fixture 的兜底清理仍执行：`backend/tests/integration/test_cypher_contract_gate.py:158-163`；模块级同步 driver 也有 teardown：`:129-131`。唯一未删的是 `User {id:'default_user'}`，但该 User 是既有 replay 写侧固定身份，当前 repo 未发现按该 User 数量做断言的测试；它不携带本用例 Concept/edge 状态，重复 MERGE 幂等。

### env / ContextVar / 命名空间污染

- `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 用 function-scoped `monkeypatch.setenv()` 设置：`backend/tests/integration/test_cypher_contract_gate.py:738`，测试结束自动恢复。
- `_current_subject_id` 在 `try/finally` 中 reset：`:750-754`。
- 两条用例的 concept/canvas/record_id 均为互相独立且带 `g21gate_` 前缀：`:684-687`、`:739-742`。
- 顺序运行下不会污染同文件其它用例；并发运行风险见 LOW-3。

## delta 探针复算

- 探针查询本身只 `MATCH ... RETURN count()`：`backend/tests/integration/test_cypher_contract_gate.py:629-638`。
- `Neo4jClient.run_query()` 真库路径只执行提交的 Cypher 并 `result.data()`：`backend/app/clients/neo4j_client.py:637-643`；所谓 metrics 更新仅在进程内字典/内存计数：`:581-598`，不写 Neo4j。
- 独立 `unscoped_canvas` / `unscoped_concept` 避免旧 API MERGE 命中本测试前半段已有的 base canvas/concept；fixture setup 又先按 gate 前缀清空旧 Node/Canvas：`backend/tests/integration/test_cypher_contract_gate.py:154-157`、`:96-105`。因此顺序执行中，提前调用 `record_score_history()` 会造成 Node/Canvas 净新增并被 count delta 抓住。
- 该探针只抓 Node/Canvas **净新增**，不抓既有节点属性改写、边新增、User、随机 Episode；注释 `:651-655` 已大体收窄，但随机 Episode 未列入盲区清单，见 LOW-1。
- 共享 7692 上若另有进程同时增删同前缀节点，前后 count 可被外部扰动；这是运行隔离问题，见 LOW-3。

# BLOCKER

无。

# HIGH

无。

# MEDIUM

无。

# LOW

## LOW-1｜“全域零写”仍留随机 Episode / User / 边-only / 属性改写逃逸面

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:629-667`
- 相关生产写面：`backend/app/clients/neo4j_client.py:1806-1820`、`:1896-1906`
- 复现思路：
  1. 把 `_resolve_entry_source()` 返回 None 后的拒写分支改为只执行一条 raw Cypher：`CREATE (e:Episode {id: randomUUID(), type: 'scoring'})`，然后照旧 `return False`。
  2. 当前断言结果：
     - Node/Canvas 前缀 count 不变；
     - `Concept {name: unscoped_concept}` 数为 0；
     - `Episode.record_id = unscoped_rid` 数为 0，因为随机 Episode 没有 `record_id`；
     - `refused is False` 通过。
  3. 测试全绿，但共享 7692 留下 scoring Episode。
- 未拦输入：
  - random UUID Episode；
  - Episode `record_id` 被 hash/random/None 化且不写 Node/Canvas；
  - User-only MERGE；
  - CONTAINS_NODE / SCORED / LEARNED 边-only 写；
  - 命中既有同键 Node/Canvas 后的属性改写。
- 对照输入：
  - 当前实现 `_resolve_entry_source()` 得 None 后在 `backend/app/services/fallback_sync_service.py:912-920` 直接返回 False，不进入图写。
- 负控输入：
  - 在隔离 fixture 内对 `(:Episode {type:'scoring'})` 做前后总量 delta，或写入带测试运行前缀的 marker 后断言不存在；再分别加 User/关系类型计数。
- 盲区：
  - 注释已从“整条零写”收窄为“Concept + 按 record_id Episode”，这点修复有效；
  - 但 `:651-655` 的未断言面枚举没有显式列出 random-id Episode。若 LOW-1 的验收只是“不得夸大证据”，可算闭合；若验收是字面全域零写，则为部分闭合。

## LOW-2｜完整优先级矩阵仍缺 vault_id-vs-env / 三源冲突；conflict 负控文案的 B 组口径不准

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:670-706`、`:719-767`
- 生产对照：`backend/app/services/fallback_sync_service.py:627-644`
- 既有 vault-only 集成门：`backend/tests/integration/test_replay_rewrite_7692.py:211-217` 删除 env，`:426-444` 只测 entry vault。
- 复现思路 A（实现重排仍全绿）：
  1. 把 `_resolve_entry_source()` 改成顺序 `group_id > env > vault_id`。
  2. 新 conflict 用例：group A 存在，仍先返回 A，通过。
  3. 新 env 用例：无 group/vault，env 被采用，通过。
  4. 既有 vault-only 用例：其 fixture 已删除 env，因此 env 为空后仍落到 vault，通过。
  5. 于是 `vault_id > env` 的优先级回归未被任何一条指定门拦住。
- 未拦输入：
  - `{vault_id: B, env: C}` 应落 B，但 env-first 实现落 C；
  - `{group_id: A, vault_id: B, env: C}` 应落 A，但可被若干非生产顺序部分通过；
  - 更一般的排列矩阵未完整锁死。
- 对照输入：
  - 当前实现顺序是 entry group → entry vault → env → quarantine：`backend/app/services/fallback_sync_service.py:627-637`。
- 负控输入：
  - 增加 `{vault_id: B}` + `monkeypatch.setenv(..., C)`，期望 B；
  - 或一条三源同冲突用例，期望 A，并同时以 B/C 作为失败时的可见区分组。
- 复现思路 B（文档口径不准）：
  - `backend/tests/integration/test_cypher_contract_gate.py:678-679` 说 vault-first 会“落到 GID_B”。
  - 实际生产 vault 分支会执行 `build_vault_group_id(vault_id, canvas_path=canvas_name)`：`backend/app/services/fallback_sync_service.py:630-644`；builder 会取 canvas stem 并追加二级 namespace：`backend/app/core/subject_config.py:259-263`。
  - 因此该输入的实际反例组是 `vault__g21gate_b__g21gate_matrix_conflict`，不是 `GID_B = vault__g21gate_b`。
  - 断言仍会红、仍能抓优先级反转；这是负控说明与生产推导不一致，不是 runtime 假绿。
- 盲区：
  - r2 点名的两个格子——group/vault 冲突与 env 正向分支——已经闭合；
  - 本条只在把 LOW-3 标题中的“完整优先级矩阵”当作验收面时计为残余。

## LOW-3｜固定 gate 前缀 + 共享 7692，对并发重复运行不具备隔离性

- 位置：`backend/tests/integration/test_cypher_contract_gate.py:89-116`、`:154-161`、`:684-687`、`:739-742`
- 复现思路：
  1. 在同一 7692 上并发启动两个进程跑本文件。
  2. 进程 A 正在 matrix conflict/env 用例中写入并回查；
  3. 进程 B 的 `gate_client` setup 执行 `_CLEANUP_QUERIES`，按全局 `vault__g21gate`、`g21gate` id/name/path 以及新加的 `record_id STARTS WITH 'g21gate_'` 删除 A 的数据；
  4. A 的 Episode/Concept 断言、delta count 或自清理可与 B 的 setup/teardown 交错，出现假红/漏清理。
- 未拦输入：
  - 同一测试文件的多进程/多 CI job 并行复用同一容器；
  - 外部进程在 delta 探针前后分别增删同前缀 Node/Canvas，造成 count 扰动。
- 对照输入：
  - 顺序运行同一文件时不受影响：function fixture 在每条测试前后清理，且本 repo 当前没有其它测试使用 `g21gate_` record_id 前缀。
- 负控输入：
  - 仿照 `backend/tests/integration/test_neo4j_replay_wire_t6b.py:121-134` 或 `backend/tests/integration/test_replay_rewrite_7692.py:103-108`，为每次运行加入一次性 run id，并把清理/计数/delta 全部绑到 run 级前缀。
- 盲区：
  - 这不是本轮首创的架构问题：本文件既有 cleanup 已是 gate 级全局前缀；
  - 但新增 Episode record_id 前缀清理与两条新图写用例扩大了并发碰撞面。若项目明确禁止并发跑同一 7692 gate，则可只作为运行纪律登记。

清零：否；B/H/M/L = 0/0/0/3
