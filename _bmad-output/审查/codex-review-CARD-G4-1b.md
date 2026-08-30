# Codex 审查存档 — CARD-G4-1b（neo4j client 层读收口）

> **批次**: BATCH-2026-08-31-第七批 / 车道 V1
> **命令**: `codex exec --sandbox read-only -c model_reasoning_effort=high`（提示词见本文件 §附录）
> **送审范围**: 明确限定读哪些文件（MEMORY `reference_codex_exec_gotchas`：cyber 误拦的真触发源是被审内容，正解是限定"让它读什么"）
> **审查重点**（卡文指定）: 镜像与 Cypher 同批同语义 / 误路由旁路 / recovery 收窄声明诚实性 / 门是否真能红

---

## Round-1（2026-08-31 03:0x）— 裁定 **FAIL**

```
结论：**FAIL**。未发现当前路由会返回“完全未过滤”的跨 vault 结果，但存在多处降级语义不一致、recovery 假空风险，以及声称能红但实际覆盖不足的门。

`HEAD=9cf0fb85ed839bb7035d023534fca222a24d6968`。本卡有 7 个 tracked 修改；`g41b_mutation_negative_controls.py` 仍是 untracked；`vault_scope.py` 未修改。

## 1. JSON 镜像与 Cypher

- [HIGH] `get_canvas_concepts` 的 JSON 镜像与 Cypher 根本不是同一查询语义。Cypher 对 `Canvas.path` 做精确匹配，并读取 `Canvas→CONTAINS_NODE→Node`；JSON 却扫描通用 `relationships`，用字符串包含判断 canvas path。[neo4j_client.py:2267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2267)、[neo4j_client.py:2320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2320)。复现：scope 内记录 `canvas_path="x/a.canvas.bak"`，查询 `"a.canvas"`；JSON 返回概念，Cypher 的 `c.path = $canvasPath` 不返回。`find_common_concepts` 两次复用该镜像，因此继承同一差异。[neo4j_client.py:2418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2418)

- [MEDIUM] associations 与 episodes 镜像只过滤一份记录级 `group_id`，Cypher 分别过滤三侧或两侧 alias，不是“逐字同语义”。[neo4j_client.py:1893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:1893)、[neo4j_client.py:1960](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:1960)、[neo4j_client.py:2475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2475)、[neo4j_client.py:2516](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2516)。反例：`r.group=A` 但关联端点或 Concept 为 B；JSON 放行，Cypher 因端点/Concept alias 过滤而拒绝。正常写侧保持一致时结果相同，但面对存量错组数据不能宣称相同可见面。

- [OK] `_CONCEPT_ID_MATCH_CYPHER` 与 `_concept_id_matches` 当前表达式本身都是“id OR name”。[neo4j_client.py:158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:158)、[neo4j_client.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:161)。但 JSON 判的是关系里的反规范化字段，Cypher 判的是实际 `Concept` 节点；只有两者一致时才真正等价。

- [OK] `read_group_filter` 与 `group_in_read_scope` 的等值/带 `__` 定界前缀规则相符，NULL/缺组均 fail-closed。[vault_scope.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/core/vault_scope.py:623)、[vault_scope.py:650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/core/vault_scope.py:650)

## 2. 误路由旁路

- [HIGH] 中途降级不会泄漏到全库，但会严重改变结果语义。[neo4j_client.py:549](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:549)、[neo4j_client.py:587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:587)：
  - `get_learning_history` 落到 history handler 后，`startDate/endDate/concept/limit` 全被忽略；handler 只读取 `userId/conceptId/group_id`，且不切 limit。[neo4j_client.py:779](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:779)
  - `get_all_recent_episodes(limit=1)` 中途降级时可返回所有 scope 内记录，因为外层也不再切片。[neo4j_client.py:2489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2489)
  - associations、canvas concepts、common concepts、score history 等中途降级全部进入 `else -> []`，不会调用各自已有的 JSON handler，导致“启动即 JSON 模式”和“运行中切 JSON”结果不同。

- [OK] 穷举本文件 16 个 `run_query` 形状后，没有未过滤读出口：
  - 1 个学习写入 → `_handle_merge_learning`；
  - 1 个 review 读 → `_handle_query_reviews`；
  - 3 个 `MATCH…LEARNED` 普通读 → scoped `_handle_query_history`；
  - 其余 11 个 Canvas/score/association 查询 → `else` 空列表。
  
  `else` 是功能性假空，但不是未过滤泄漏。[neo4j_client.py:588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:588)

- [OK] `_handle_query_history` 升 fail-closed 没打断本文件内三个正常 LEARNED 读：它们都经 `read_scope_params` 注入 `group_id`。[neo4j_client.py:1042](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:1042)、[neo4j_client.py:1148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:1148)、[neo4j_client.py:2466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:2466)

## 3. Recovery 声明

- [HIGH] 显式传 `default_vault_group_id()` 会把派生值重新标记成“explicit”，从而绕过 `vault:default` 的派生 fail-closed 检查。[memory_service.py:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/services/memory_service.py:349)、[vault_scope.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/core/vault_scope.py:428)、[vault_scope.py:548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/core/vault_scope.py:548)。复现路径：active vault 配置缺失 → `default_vault_group_id()` 产出 `vault:default` → client 将其按显式作用域放行 → 查询污染桶空结果 → `_episodes_recovered=True`，以后不再重试。这与“作用域解析不出即上抛”声明不一致。

- [MEDIUM] “现网返回逐字节相同”仅在旧查询与新查询的有序 top-1000 序列恰好一致时成立；“全库当时只有一条且属于 active vault”是足够前提，但不是代码不变量。[memory_service.py:342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/services/memory_service.py:342)、[cypher-read-contract.md:86](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/.claude/rules/cypher-read-contract.md:86)。任何其他 vault 新增较新记录、相同时间戳排序不稳定，或超过 limit，逐字节声明都可能失效；因此它只能是 2026-08-30 快照结论，不能作为持续保证。

- [MEDIUM] “Neo4j 不可用会优雅降级”的异常范围被写得过宽；实际只吞 `RuntimeError/ConnectionError/TimeoutError`。[memory_service.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/services/memory_service.py:411)。Neo4j 抛出的其他 `Neo4jError`、`ValueError` 等会穿透 `_recover_episodes_from_neo4j`，进而使 `MemoryService.initialize()` 失败；这不是空历史降级。

- [OK] 如果 client 真正抛出 `VaultScopeUnresolved`，它会穿透 recovery 的窄捕获；concept-history 端点也在 `try` 外完成 vault 解析，因此显式 vault 冲突的 409 不会被改写成 500。[memory_service.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/services/memory_service.py:411)、[memory.py:293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/api/v1/endpoints/memory.py:293)

## 4. 门是否真能红

- [HIGH] id/name 同语义门杀不死最关键的 `OR → AND` 变异。单测只查两个子串都存在；真库 seed 又把 `c.id` 设置成与 `c.name` 相同。[test_neo4j_client.py:977](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/unit/test_neo4j_client.py:977)、[test_cypher_contract_gate.py:1348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1348)。把 Cypher 改成 `c.id = $conceptId AND c.name = $conceptId` 后，这些门仍会绿，但生产 `c.id=NULL、c.name=目标` 会再次恒空。

- [HIGH] Gate 7.5 声称覆盖“四个 JSON 镜像与 Cypher 同语义”，实际循环只测 `all_recent_episodes`、`learning_history`、`concept_history`；四个指定镜像中只覆盖了 episodes。[test_cypher_contract_gate.py:1471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1471)。association、canvas concepts、common concepts 没有 Cypher/JSON 对拍，因此抓不到第 1 节的现存差异。

- [HIGH] Gate 7.6 只实际触发 `get_all_recent_episodes`，且数据量小于 `limit=500`；它测不到 `get_learning_history` 丢日期/概念过滤，也测不到 episodes 丢 limit，更测不到其余查询落 `else=[]`。[test_cypher_contract_gate.py:1520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1520)

- [MEDIUM] `find_common_concepts` JSON 行为门只有“跨 vault 应为空”的否定断言，没有同 vault 共同概念的正向对照；把 common handler 写死为 `return []` 仍可通过。[test_neo4j_client.py:890](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/unit/test_neo4j_client.py:890)

- [MEDIUM] mutation 脚本把“任一整文件测试失败”算作该变异被杀，无法证明声称的具体门红了。[g41b_mutation_negative_controls.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:260)。尤其 `episodes-json-unscoped` 不会影响 Gate 7.6 的中途降级路径——后者走 `_handle_query_history`，不是 `_get_all_recent_episodes_json`；脚本仍可因 Gate 7.5 或 unit 失败而报告 RED。[g41b_mutation_negative_controls.py:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:121)

- [OK] 当前 mutation 锚点至少有 `count == 1` 防护，找不到或多处命中会立即退出，未见可静默命中错误位置的锚点。[g41b_mutation_negative_controls.py:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:248)

- [MEDIUM] mutation 脚本当前是 untracked，`git diff HEAD` 完全不包含它；若按当前 tracked diff 交付，“12 类机械变异负控”不会进入提交。

本次为严格静态只读审查；没有执行 mutation 脚本，因为它会原地改写生产源码再恢复。[g41b_mutation_negative_controls.py:287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:287)


```

---

## Round-1 整改记录（逐条，2026-08-31）

> 判定原则：**先认账再反驳**。下面每条都给"是否成立 / 怎么改 / 改完哪道门能红"。

| # | Codex 结论 | 我的裁定 | 处置 |
|---|---|---|---|
| §1 HIGH | `get_canvas_concepts` 的 JSON 镜像用**子串包含**判 canvas path，Cypher 是精确相等 | **成立**（既有形态，但我在 docstring/验收单里宣称"同语义"= 夸大） | 镜像改精确相等 `rel.get("canvas_path") == canvas_path`；新增单测 `test_mirror_path_match_is_exact_like_cypher`（用"超串路径"当探针，含 associations / canvas_concepts 两族） |
| §1 MEDIUM | assoc / episodes 镜像只过滤**一份记录级** `group_id`，Cypher 过滤三侧/两侧 alias，不是"逐字同语义" | **成立** | 不改行为（JSON 存储是反规范化的，一条记录只有一个 group，per-alias 归属**表达不出来**）；改**措辞**：两个镜像 docstring 明写这条上限，说明"本仓写侧数据下两侧相同、存量错组数据下 Cypher 更严" |
| §1 OK | `_CONCEPT_ID_MATCH_CYPHER` / `_concept_id_matches` 语义一致 | 采纳 | — |
| §2 HIGH | 中途降级不泄漏，但**改变结果语义**：learning_history 丢日期/概念过滤；episodes 丢 limit；其余查询落 `else -> []` | **成立**（泄漏面确认已闭，但 limit 那条是我自己的"同语义"承诺没兑现） | `get_all_recent_episodes` 外层补 `[:limit]`；`_handle_query_history` 尊重 `params["limit"]`；门 7.6 加"降级后 limit 必须生效"断言。**date/concept 过滤与 `else -> []` 不修**：那要给模拟器补一套查询解析，属另一张卡，已登记（见验收单 §四） |
| §2 OK | 穷举 16 个 `run_query` 形状，无未过滤读出口；fail-closed 未打断正常读 | 采纳（与我方判断一致） | — |
| §3 HIGH | 显式传 `default_vault_group_id()` 会被当"explicit"，**绕过** `vault:default` 污染桶的 fail-closed → 配置断裂时"装 0 条 + `_episodes_recovered=True` + 永不重试" | **成立，且是本轮最重的一条**（我在规划阶段判断过这个风险并认为可接受——判错了：漏看了"不再重试"这半） | 改为在**全新空 `contextvars.Context()`** 里调 `require_read_group(None)`：新 Context 无 ContextVar 赋值 ⇒ 走 **active vault 派生**分支（方案甲要的进程级语义）＋ 污染桶 fail-closed。新增门 `test_unconfigured_active_vault_fails_closed_not_silent_empty` |
| §3 MEDIUM | "现网返回逐字节相同"只是快照结论，不是代码不变量 | **成立** | docstring + 契约文档 + 验收单三处都改成"2026-08-30 快照结论"，并写明它失效的三种情形（别的 vault 有更新记录 / 超 limit / 同 timestamp 排序不稳） |
| §3 MEDIUM | "Neo4j 不可用会优雅降级"的异常范围被写宽了；`Neo4jError`/`ValueError` 会穿透 | **成立**（既有形态） | 不放宽 `except`（放宽会吞 `VaultScopeUnresolved`）；验收单 §四已登记为独立收债卡 |
| §4 HIGH | id/name 门杀不死 `OR → AND` 变异（seed 把 `c.id` 设成等于 `c.name`） | **成立，真死门** | 新增 `g41b_idname_seed`：一条**没有 `c.id`**（生产形态，fixture 自证 `c.id IS NULL`）＋ 一条 `id != name`；两条门分别锁 name 分支与 id 分支；新增变异 `ch-and-not-or` |
| §4 HIGH | 门 7.5 声称覆盖"四个 JSON 镜像"，实际只覆盖 episodes 一个 | **成立**（措辞夸大） | 门 7.5 docstring 改为如实声明覆盖 3 条 LEARNED 族读（4 个镜像里只含 `_get_all_recent_episodes_json`），并指明另三个镜像由单测的路径对称门 + 逐 alias 片段门覆盖、原因是卡文 (d) 禁造真库种子 |
| §4 HIGH | 门 7.6 只触发 episodes 一条，且数据量 < limit | **成立** | 扩到三种形状（episodes / learning_history / concept_history，含 A 查 B 的交叉零泄漏），并加 `limit=2` 断言 |
| §4 MEDIUM | `find_common_concepts` JSON 门只有否定断言，写死 `return []` 也能过 | **成立** | 加正向对照：本 vault 在两块白板上共有 `mine-root`，断言 `common == {"mine-root"}` |
| §4 MEDIUM | 变异脚本把"整文件有失败"算作被杀，证明不了**指定的那道门**红了 | **成立** | 脚本加 `expect_red_tests`：解析 `-rf` 短摘要，指定门未出现在失败清单里即判**死门**并点名 |
| §4 MEDIUM | 变异脚本 untracked，`git diff HEAD` 不含它 | 事实正确，非缺陷 | 提交时 `git add` 两个新脚本 |
| §4 OK | 变异锚点有 `count == 1` 防护 | 采纳 | — |

---

## Round-2（定点复核，2026-08-31）— 裁定 **不可合并**（Q1/Q4 PASS，Q2/Q3/Q5/Q6 FAIL）

```
Q1. [PASS] 空 `Context` 中 `get_current_subject_id()` 只能取得默认值，因此跳过 explicit 分支并调用 active-vault 派生，未配置时的 `vault:default` 会抛错（真实配置名就是 `default` 时按设计放行）；这里只同步执行解析且使用全新 Context，不受 Context 重入限制，也没有把后续异步调用放入缺失调用方 ContextVar 的环境。`backend/app/services/memory_service.py:366-382`；`backend/app/core/vault_scope.py:466-486`；`backend/app/core/vault_scope.py:548-571`

Q2. [FAIL] `==` 修掉了子串误命中，但镜像仍扫描无关系类型约束的通用 `relationships`，且 `rel.get("source") == canvas_path` 未证明 `source` 就是 `Canvas.path`、也没有测试覆盖，所以仍可返回 Cypher 的两种 Canvas 关系均不会返回的记录。`backend/app/clients/neo4j_client.py:2285-2299`；`backend/app/clients/neo4j_client.py:2338-2349`；`backend/tests/unit/test_neo4j_client.py:941-948`

Q3. [FAIL] 三条路径的 `limit` 上限已落实，但带 `startDate`、`endDate` 或 `concept` 的 `get_learning_history` 中途降级仍忽略过滤并可能多返，因此完整条数语义尚不一致；这三个遗漏已明确登记，未发现其他未登记的参数丢失。`backend/app/clients/neo4j_client.py:769-843`；`backend/app/clients/neo4j_client.py:1137-1147`；`backend/app/clients/neo4j_client.py:2517-2523`；`_bmad-output/审查/codex-review-CARD-G4-1b.md:86`

Q4. [PASS] `OR → AND` 会使“无 `c.id`、按 name 查”和“`id != name`、按 id 查”两条真库门同时变红，JSON 单测也会红，已经足以区分并锁住 OR 的两支。`backend/tests/integration/test_cypher_contract_gate.py:1597-1635`；`backend/tests/integration/test_cypher_contract_gate.py:1639-1669`；`backend/tests/unit/test_neo4j_client.py:1028-1044`

Q5. [FAIL] 门 7.6 确实执行了三种 LEARNED 形状，但 limit 只在 episodes 上断言，而该入口外层自身切片，抓不到 `_handle_query_history` 丢 limit；门 7.5 虽承认只真库对拍一个镜像，却仍声称另三个镜像的 Cypher↔JSON“一致性”已由路径门和 alias 片段门覆盖，实际这些门不能证明整体查询语义。`backend/tests/integration/test_cypher_contract_gate.py:1477-1483`；`backend/tests/integration/test_cypher_contract_gate.py:1552-1583`；`backend/app/clients/neo4j_client.py:840-843`；`backend/app/clients/neo4j_client.py:2522-2523`

Q6. [FAIL] `expect_red_tests` 比整文件判红更强，但仍只是 nodeid 子串匹配：参数化测试的任一兄弟 case 或同名测试中的无关断言失败即可满足，而且 `episodes-json-unscoped` 只要求 unit 镜像门红，故其声称的 7.5/误路由门即使是死门，脚本仍会判 RED。`backend/scripts/g41b_mutation_negative_controls.py:153-168`；`backend/scripts/g41b_mutation_negative_controls.py:311-317`；`backend/scripts/g41b_mutation_negative_controls.py:358-368`

总裁定：不可合并——HIGH-1 的镜像语义仍未闭合，且门 7.5/7.6 与变异脚本仍存在可证明的覆盖夸大和假 RED 路径。


```

### Round-2 整改记录

| Q | Codex 结论 | 我的裁定 | 处置 |
|---|---|---|---|
| Q1 | 空 `Context` 方案正确走 derived 分支、无重入/缺 ContextVar 问题 | PASS，采纳 | — |
| Q2 | `==` 修掉了子串误命中，但镜像仍扫通用 `relationships`，`rel.get("source")` **未证明**是 `Canvas.path`，且无测试覆盖 | **成立，而且追下去更硬**：全仓唯一往 `self._data["relationships"]` 写记录的是 `_handle_merge_learning`，它写的键里**根本没有 `canvas_path`／`source`** ⇒ 这个镜像在真实数据上**恒空**，是结构性死分支 | ① 删掉无写侧的 `rel.get("source")` 匹配（R3 反对的"来源不可证标识符"）；② docstring 如实写明镜像**不是**语义等价、本卡**不宣称**等价，对这一族**只保证作用域收口**；③ 验收单 §(d) 与门 7.5 同步改口径 |
| Q3 | `limit` 已对齐，但 `startDate/endDate/concept` 中途降级仍被丢弃 | **成立**（我原本登记为"另立卡"，但实测只需 ~15 行且只动模拟器，属本卡"同语义"承诺范围，不该外推） | `_handle_query_history` 补三个过滤，语义逐条对齐 Cypher（时间用 ISO 串字典序＝时序；无 timestamp 的记录不放行，与 Cypher 的 NULL 比较不满足 WHERE 同口径）；门 7.6 加 concept 与 startDate 两条降级断言；新增变异 `history-handler-drop-date-concept` |
| Q4 | id/name 门足以杀 `OR → AND` | PASS，采纳 | — |
| Q5 | (a) limit 断言挂在 `get_all_recent_episodes` 上，而它自己有外层切片，**抓不到** handler 丢 limit；(b) 门 7.5 仍声称另三个镜像"一致性已由路径门+alias 门覆盖" | **两条都成立**。(a) 是判据放错位置的典型——探针挂在有兜底的入口上，等于没探 | (a) limit 断言改挂 `get_learning_history`（**无**外层切片，是唯一能抓到 handler 的入口），episodes 那条保留但降级为"外层切片仍在"的辅助断言；(b) 门 7.5 docstring 删掉"一致性已覆盖"，改为明写"**没有任何门在证明另三个镜像与 Cypher 语义等价，本卡不做这个宣称**"，并给出结构性原因 |
| Q6 | `expect_red_tests` 仍是 nodeid **子串**匹配（`test_foo` 会被 `test_foo_bar` 满足）；`episodes-json-unscoped` 只要求 unit 门红，7.5/误路由门即使是死门也判 RED | **成立** | ① 改为 `::` 之后**整段**比较（spec 带 `[...]` 时可精确指定参数化某一条）；② `episodes-json-unscoped` 同时要求真库对拍门 `test_g41b_json_mirror_visibility_equals_cypher` 变红；③ 残余上限**如实写进脚本 docstring**：判据粒度是"这条测试红了"，不是"红在我期望的那句断言上"——再收紧要比对失败文本，会把门与断言措辞耦死，不做 |

> **副产品**：精确匹配上线后，脚本立刻抓出我在新增变异里把门名写成 `test_g41b_midflight_fallback_stays_scoped`（真名是 `..._misroute_stays_scoped`）——子串匹配时代这种笔误会被"某处有失败"掩盖过去。

---

## Round-3（2026-08-31）— 裁定 **不可合并**（Q2' PASS；Q3'/Q5'/Q6' FAIL）

```
Q2'. [PASS] 获准范围内唯一生产写点 `_handle_merge_learning` 的关系字段确无 `canvas_path/source`，镜像已删除 `source` 分支并明确只保证作用域收口、不宣称 Cypher 等价，表述不再夸大；`backend/app/clients/neo4j_client.py:643-676,2341-2357,2385-2391`。

Q3'. [FAIL] 无 timestamp 时拒绝及大小写包含语义一致，但直接做 ISO 字符串比较未规范化类型/时区，而写侧 Cypher 使用 temporal `datetime()`、边界参数允许任意 `datetime.isoformat()`，混合偏移量时字典序不等于实际时序；`backend/app/clients/neo4j_client.py:810-840,914-917,1161-1169`。

Q5'. [FAIL] `_rearm()` 与无外层切片的 learning-history limit 探针均有效，但门 7 总述及 7.5 标题仍笼统宣称“镜像与 Cypher 同语义”，与正文承认另三个镜像未验证等价相冲突；`backend/tests/integration/test_cypher_contract_gate.py:1293,1478-1498,1565-1643`。

Q6'. [FAIL] 真库对拍门和函数名精确匹配已落实，但未带 `[...]` 的参数化门仍可由兄弟 case 满足，且顶层仍声称 `episodes-json-unscoped` 会杀死未被列入必红清单的误路由门；同测试其他断言误红的残余虽在 helper docstring 中诚实披露，整体仍存在死门判 RED 路径；`backend/scripts/g41b_mutation_negative_controls.py:23,157-160,348-363`，`backend/tests/unit/test_neo4j_client.py:771-791`。

总裁定：不可合并——Q3' 的时间边界尚未等价，Q5'/Q6' 仍有覆盖宣称与实际判据不一致。
```

## Round-4（2026-08-31）— 裁定 **不可合并**（Q6'' PASS；Q3''/Q5'' FAIL）

```
[FAIL] Q3''：混合时区比较本身正确：`_as_utc()` 将 naive 当 UTC、aware 转 UTC（[neo4j_client.py:170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:170)），探针确实构造了字典序与时序相反的数据（[test_neo4j_client.py:1028](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/unit/test_neo4j_client.py:1028)）；变异精确恢复字符串比较并指定该测试（[g41b_mutation_negative_controls.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:211)），逻辑上必杀，当前测试也实跑 1 passed。但仍有两处不闭合：只有记录时间 `ts` 解析失败会拒绝；`startDate/endDate` 解析失败得到 `None` 后过滤被跳过、记录仍可放行（[neo4j_client.py:871](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:871)）。另外“temporal 与 string 比较结果为 null”不准确（[neo4j_client.py:852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:852)）：Neo4j 对异型值使用类型层级排序，temporal 排在 string 前面，不是返回 null；因此 start 下界恒不满足、end 上界恒满足。日期过滤确实坏且两侧不等价，但所写原因错误。[Neo4j 官方比较规则](https://neo4j.com/docs/cypher-manual/5/values-and-types/ordering-equality-comparison/)

[FAIL] Q5''：门 7 总述已经准确限定为 LEARNED 三条读，并明确另外三个镜像没有语义等价证明（[test_cypher_contract_gate.py:1293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1293)）；正文也限定为三条读的“可见面”相等（[test_cypher_contract_gate.py:1485](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1485)）。但 7.5 标题仍笼统写着“JSON 镜像与 Cypher 同语义”（[test_cypher_contract_gate.py:1482](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1482)），helper docstring 也重复该宣称（[test_cypher_contract_gate.py:1310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1310)）。实际断言只比较 `_names()` 可见集合，没有覆盖字段、排序、日期过滤等完整语义（[test_cypher_contract_gate.py:1510](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1510)），措辞仍过宽。

[PASS] Q6''：collect-only 确认两个完整参数 ID 与脚本逐字一致（[g41b_mutation_negative_controls.py:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:123)）；matcher 对带 `[...]` 的规格执行完整 tail 相等，并在任一指定门未失败时强制判 GREEN/死门（[g41b_mutation_negative_controls.py:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:385)、[g41b_mutation_negative_controls.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:443)）。`episodes-json-unscoped` 顶层说明也已明确不会杀误路由门（[g41b_mutation_negative_controls.py:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:21)）。当前没有未声明的“指定测试没红却判 RED”路径；仍可能由同一测试中的另一条断言先失败而算命中，但该测试粒度上限已如实写明（[g41b_mutation_negative_controls.py:393](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:393)）。

总裁定：不可合并
```

### Round-3 / Round-4 整改记录

| Q | Codex 结论 | 我的裁定 | 处置 |
|---|---|---|---|
| Q2' | 镜像事实陈述准确、宣称不再夸大 | PASS | — |
| Q3' | ISO **字符串**比较在混合时区偏移下字典序≠时序 | **成立** | 新增 `_as_utc()`：ISO/datetime → aware UTC（naive 按 UTC 解释并点名理由）；新增探针 `test_degraded_date_filter_is_timezone_correct`（用 `+08:00` vs `+00:00` 这对**字典序与时序相反**的值）+ 变异 `history-handler-string-time-compare` |
| Q5' | 门 7 总述与 7.5 标题仍笼统写"镜像与 Cypher 同语义" | **成立** | 门 7 文件头改为点名"只覆盖 `_get_all_recent_episodes_json`，另三个镜像没有任何门在证明语义等价，本卡不做这个宣称" |
| Q6' | `expect_red_tests` 仍是函数名级，参数化门可被兄弟 case 满足；`episodes-json-unscoped` 的顶层说明错误 | **成立** | 参数化门改用**完整 param id**（`...[g21gate_g41a_xc-False]` / `...[get_concept_history-kwargs4-branch_aliases4]`）；脚本顶层 docstring 改成"**不**会红误路由门"的正确说法 |
| Q3''(a) | `startDate/endDate` **解析失败**时 `lo/hi` 为 None，过滤被整个跳过、记录仍放行 | **成立**（同一个"把没生效当成没限制"的坑，我在别处堵了这里没堵） | 传了边界就必须能解析：解析失败 → `logger.error` + 拒绝该条；新增门 `test_degraded_unparseable_date_bound_fails_closed`（带正向对照）+ 变异 `history-handler-bound-parse-lenient` |
| Q3''(b) | 我写的"temporal 与 string 比较结果为 null"**不准确**，Neo4j 按类型层级排序，temporal 排在 string 前 | **不成立——实测反驳**。2026-08-31 于 7692 实跑：`WITH datetime('2026-06-01T00:00:00Z') AS t, '2026-01-01T00:00:00' AS lo RETURN t >= lo, (t >= lo) IS NULL` → **`null, true`**。Codex 引的"跨类型有序"规则管的是 **ORDER BY 排序上下文**，不是 `<`/`>=` **比较运算符**——后者对不可比类型返回 null。两者容易混为一谈 | 结论不改（原说法正确），但把**实测 Cypher 与结果**写进 docstring，并点名"排序规则 ≠ 比较运算符"，免得后人再争一轮 |
| Q5'' | 7.5 的**标题行**与 helper docstring 仍写"同语义"；实际断言只比 `_names()` 可见集合，不覆盖字段/排序/日期过滤 | **成立** | 标题改成"**可见面**对拍"，正文加"本门比什么、不比什么"：比 concept 名集合，**不比**字段完整性、排序、分页、其余过滤 |
| Q6'' | 参数 id 逐字一致、matcher 正确、残余上限已诚实声明 | PASS | — |

> **这一轮的方法论要点**：Q3''(b) 是 Codex 报错的一条。MEMORY 里有"别把 agent 结论照单全收"的教训，也有"我自己写错边界声明"的教训——两种风险同时在场时，唯一出路是**去真库跑一条能分辨两种说法的查询**。跑完 3 秒，比争一轮便宜。

---

## Round-5（2026-08-31）— 裁定 **不可合并**（Q3'''(a) PASS / Q3'''(b) **PASS——Codex 独立复现后撤回自己的说法** / Q5''' FAIL）

```
Q3'''(a) [PASS] 运行时缺口已闭合：畸形边界触发 `ERROR` 并拒绝候选记录；合法边界仍正常放行。回归测试包含正向对照，定向实跑结果为 `1 passed`。变异负控准确替换 fail-closed 条件，并指定该测试必须变红；因只读约束未执行会原地改源码的变异脚本。[neo4j_client.py:880](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:880)（880–902）、[test_neo4j_client.py:1058](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/unit/test_neo4j_client.py:1058)（1058–1088）、[g41b_mutation_negative_controls.py:210](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/scripts/g41b_mutation_negative_controls.py:210)（210–220）。

Q3'''(b) [PASS] 你的说法和实测是对的。已独立在 Neo4j `5.26.23` 的 7692 容器复现：`t >= lo` 返回 `null`，`(t >= lo) IS NULL` 返回 `true`。跨类型层级用于混合类型排序，不能据此推导该 `>=` 表达式为布尔值；[Neo4j 5 官方比较与排序说明](https://www.neo4j.com/docs/cypher-manual/5/values-and-types/ordering-equality-comparison/)也区分排序层级与可直接比较类型。因此无需提供反例 Cypher。[neo4j_client.py:852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/app/clients/neo4j_client.py:852)（852–868）。

Q5''' [FAIL] 实际断言和正文已经限定为 concept 名集合：`_json_client` 明说不是完整查询语义，测试正文明确排除字段完整性、排序、分页及其余过滤，断言也确实只是 `_names()` 集合相等。但门 7.5 的分节标题仍是“JSON 镜像与 Cypher 同语义”，并未改成你所说的“可见面对拍”，与正文限定冲突。[test_cypher_contract_gate.py:1310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1310)（1310–1315）、[test_cypher_contract_gate.py:1483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1483)、[test_cypher_contract_gate.py:1491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1491)（1491–1495）、[test_cypher_contract_gate.py:1542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1542)（1542–1545）。

总裁定：不可合并。
```

### Round-5 整改记录

| Q | 结论 | 处置 |
|---|---|---|
| Q3'''(a) | PASS —— 边界解析失败已 fail-closed，门与变异齐备 | — |
| Q3'''(b) | **PASS，且 Codex 撤回了 round-4 的指控**：它在 Neo4j `5.26.23` 的 7692 容器上独立复现，确认 `t >= lo` 返回 `null`、`(t >= lo) IS NULL` 返回 `true`；并同意"跨类型层级用于混合类型**排序**，不能据此推导 `>=` 表达式为布尔值" | 无需改动。**这条值得记住**：面对"我可能写错了边界声明"与"agent 可能报错"两种风险同时在场，正解是去真库跑一条能分辨两说的查询——3 秒钟结束争论 |
| Q5''' | FAIL —— **分节标题**（`# ── 7.5 JSON 镜像与 Cypher 同语义`）没跟着正文一起改，与正文限定自相矛盾 | 标题改为"LEARNED 族三条读: 降级前后的**可见面**对拍 (不是完整语义等价)"；`grep 同语义` 全文归零 |

---

## Round-6（2026-08-31）— 终裁 **可合并** ✅

```
[PASS]

依据：

- 全文件检索“同语义 / 语义等价 / 完全等价”仅命中 4 处，均为明确否定或范围限定，没有过宽宣称：[test_cypher_contract_gate.py:1296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1296)、[1483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1483)、[1495](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1495)、[1505](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1505)。
- 分节标题准确限定为“可见面对拍”，并否定完整语义等价：[test_cypher_contract_gate.py:1483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1483)。
- `_json_client` docstring 明确只比较 concept 名集合，不是完整查询语义：[test_cypher_contract_gate.py:1313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1313)。
- 门 7 文件头限定为 LEARNED 三条读，并明确另外三个镜像未证明 Cypher 语义等价：[test_cypher_contract_gate.py:1293](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1293)。
- 测试正文声明仅比较 `_names()` concept 名集合，排除字段、排序、分页及日期过滤；实际断言也确为 `_names(cypher_rows) == _names(json_rows)`：[test_cypher_contract_gate.py:1491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1491)、[1542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend/tests/integration/test_cypher_contract_gate.py:1542)。

总裁定：可合并
```

---

## 六轮小结

| 轮 | 裁定 | 提出 | 成立 | 我方反驳并被采纳 |
|---|---|---|---|---|
| 1 | FAIL | 5 HIGH + 6 MEDIUM | 11/11 | 0 |
| 2 | 不可合并 | Q2/Q3/Q5/Q6 FAIL | 4/4 | 0 |
| 3 | 不可合并 | Q3'/Q5'/Q6' FAIL | 3/3 | 0 |
| 4 | 不可合并 | Q3''/Q5'' FAIL | 2 条里 **1 条成立、1 条被实测反驳** | Q3''(b) |
| 5 | 不可合并 | Q5''' FAIL | 1/1 | —（Codex 主动撤回 round-4 的 Q3''(b) 指控） |
| 6 | **可合并** ✅ | — | — | — |

**六轮里唯一一次「我是对的」**：round-4 的 Q3''(b)（temporal vs string 比较返回 null，还是按类型层级排序）。解决办法不是辩论，是去 7692 跑三秒钟的查询——round-5 Codex 独立复现后自己撤回了。其余 21 条**全部成立**，包括我在规划阶段主动权衡过、判断"可接受"的那条（recovery 显式传参绕过污染桶 fail-closed）——**当时漏看了 `_episodes_recovered=True` 之后不会重试**。
