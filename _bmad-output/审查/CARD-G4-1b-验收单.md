# CARD-G4-1b 验收单 — neo4j client 层读收口（R4 存量清零）

> **批次**: BATCH-2026-08-31-第七批 / 车道 V1（`card/v1-clientread`）
> **上游**: CARD-G4-1a 验收单 §(f) 移交清单 + `G2-1-cypher-audit-2026-08-27.md` §5
> **契约**: `.claude/rules/cypher-read-contract.md` R1 / R4 / R5
> **日期**: 2026-08-31
> **硬边界**: 不改 `vault_scope.py` 本体（只调用）；不碰 `memory_service` 写侧；7691 现网**只读**，写测试全在 7692；`exam_service` / `verification_service` / `review_service` 未触碰。

---

## 〇、一句话结论

`neo4j_client.py` 里最后 5 个无作用域业务读 + 4 个 JSON 镜像全部封堵，R4 未封堵存量**清零**；顺手修掉 `get_concept_history` 的名实不符（该端点此前**恒返回空 timeline**，现在开始可能有数据）；启动恢复按方案甲收窄为 active vault 前缀族。**19/19 机械变异被杀**（含独立审计后新增的 3 条），且每条都验证了「指定的那道门」变红（不是「某处有失败」）。

Codex **六轮**审查，round-6 终裁 **可合并**（BLOCKER/HIGH 清零）。共提出 22 条，**21 条成立并已整改**，1 条被真库实测反驳（Codex 复现后自行撤回）。逐条整改记录见 `codex-review-CARD-G4-1b.md`。

最重的一条是我在规划阶段主动权衡过、并判断"可接受"的：recovery 把自己算出的 active vault 组当**显式**入参传下去，会绕过 `vault:default` 污染桶的 fail-closed —— **我当时漏看了后半段**：配置坏掉的进程会走成「装 0 条 + `_episodes_recovered=True` + **永不重试**」，把配置断裂伪装成没有数据。

---

## 一、用户可感说明（三条）

| 变化 | 用户会看到什么 |
|---|---|
| **`/api/v1/memory/concepts/{id}/history` 从恒空变可能有数据** | 这个端点以前**无论有没有数据都返回空 timeline** —— client 侧同名方法不管连没连 Neo4j 都只读 JSON 模拟器，而真实部署下那是个空壳。现在它真的去查图了。**如果之前有人把"这个概念没有历史"当成事实，那个结论是假的。** 另注：概念点查按 id **或名字**命中，因为生产写侧从不给 Concept 落 `id`，只按 id 查等于没修 |
| **重启后的学习历史只装本 vault** | 以前重启恢复是**全库扫**（所有 vault 的 episode 都进同一个进程缓存）。现在只装 active vault 及其子组。**现网当下看不出差别** —— 2026-08-30 实测全库唯一的 LEARNED 边就在 active vault 的 punycode 子组里，装载结果逐字节相同。多 vault 部署下才有差别，而那正是要修的泄漏 |
| **Neo4j 挂掉时的降级读也开始隔离了** | 以前"把 Neo4j 弄挂"能让刚封堵的跨 vault 面整个回来（降级模拟器不过滤）。现在两条路径的**作用域规则**一致——注意这说的是"能看到哪些概念"，**不是**"两条路径完全等价"（字段/排序等其余语义各有各的门，关联族那三个镜像更是在真实数据上恒空，见 §(d)） |

---

## 二、完成条件逐条对照

### (a) 5 读方法 + 4 JSON 镜像 + `_handle_query_history` fail-closed ✅

| # | 方法 | 审计编号 | 过滤的 alias | 备注 |
|---|---|---|---|---|
| 1 | `get_concept_history` | G2-2 移交项 2 | `r` / `c` | 新增真实 Cypher 分支（见 (b)） |
| 2 | `get_canvas_associations` | #11/#12/#13/#14 | `source` / `r` / `target` | 原四分支合并为按需拼接 WHERE |
| 3 | `load_all_canvas_associations` | —（#11 族） | 同上（透传） | "all" = 本作用域内全部 |
| 4 | `get_canvas_concepts` | #17 | 支1: `c`/`cn`/`n`；支2: `c`/`n`/`concept` | UNION 两支各自过滤 |
| 5 | `find_common_concepts` | #18 | `c1`/`cn1`/`n1` + `c2`/`cn2`/`n2` | 交集两边同一可见面 |
| 6 | `get_all_recent_episodes` | #19 | `r` / `c` | `u:User` 是跨 vault 共享身份节点，无 group_id 属性，不参与过滤 |
| M1 | `_get_associations_json_fallback` | 镜像 | `assoc.group_id` | |
| M2 | `_get_canvas_concepts_json_fallback` | 镜像 | `rel.group_id` | 停读无归属的 `canvas_concepts` 映射（见下） |
| M3 | `_find_common_concepts_json_fallback` | 镜像 | 透传 scope 给两边 | |
| M4 | `_get_all_recent_episodes_json` | 镜像 | `rel.group_id` | |
| H | `_handle_query_history` | 路由落点 | `params["group_id"]` | 升 fail-closed（`logger.error` + `[]`），对齐 `_handle_query_reviews`；并尊重 `params["limit"]`（Codex round-1 HIGH-2） |

**范式一致性**：Cypher 侧抄 `get_learning_history:1044-1058`（`read_scope_params` + 逐 alias `read_group_filter`），镜像侧抄 `_get_learning_history_json:1098-1103`（`require_read_group` + `group_in_read_scope`）。

**两处需要点名的判断（都写进了 docstring）**：

1. **`canvas_concepts` 映射表停止读取**。`_get_canvas_concepts_json_fallback` 原来还读 `self._data["canvas_concepts"]`（形如 `{path: [names]}`），这张表**不带任何归属信息**，无处施加 scope。处置是**停读并记录理由**，而不是"当作本 vault 的放行"——后者在多 vault 下就是按同名 path 串读。全仓 grep 确认：**零写侧、零其它读者、零测试引用**，不是功能损失。
2. **UNION 第二支的两个关系类型不过滤**。`CONTAINS` / `HAS_CONCEPT` / `LearningNode` 全仓**没有任何写侧**（2026-08-31 于 7692 `EXPLAIN` 实测服务端告警 `relationship type does not exist` / `label does not exist`）。给一个恒不存在的属性加等值过滤，只会把这条**本就结构性死掉**的分支变成"恒空"，掩盖它是死分支的事实——那是假门。三个**节点** alias 全过滤，R1 的全覆盖由此成立，不依赖"关系不跨组"这个不可证前提。

### (b) `get_concept_history` 名实一致修复 ✅

- **client**：补真实 Cypher 分支（`get_learning_history` 模板 + 概念点查），JSON 路径降级为**只在 `_use_json_fallback` 时**走的 fallback。
- **概念点查按 `c.id` OR `c.name`**（`_CONCEPT_ID_MATCH_CYPHER`）。理由写在常量的 docstring 里：生产写侧 `create_learning_relationship` 的 MERGE 身份是 `{name, group_id}`，**从不落 `c.id`**；而调用方手上能拿到的标识符恰恰只有名字（`get_review_suggestions` / `get_learning_history` 返回的 `concept_id` 就是 `c.id`，生产数据上恒 null）。只按 id 点查 = 换了真 Cypher 之后**仍然恒空**，等于修了个寂寞。JSON 镜像 `_concept_id_matches` 与之逐字同语义。
- **端点**：`endpoints/memory.py` 的 `get_concept_history` 加 `vault_id` / `subject_id` / 兼容 `group_id` 三参 + `_resolve_vault_group_id(...)` 注入 ContextVar（与 `:342` review-suggestions 同款，解析调用放在 `try` **之外**，避免 409 被折成 500）。
- **service**：`memory_service.get_concept_history` 加 `group_id` 透传。

> **产品可见变化（UAT 要点名）**：该端点从"恒 EMPTY"变"可能有数据"。

### (c) `get_all_recent_episodes` + recovery 方案甲 ✅

- client 加 `group_id` 参数，Cypher 与镜像同批。
- `memory_service._recover_episodes_from_neo4j` 在一个**全新的空 `contextvars.Context()`** 里调 `require_read_group(None)`。理由（写进 docstring）：
  - **为什么不能直接走默认推导链**：`require_read_group(None)` 会先看 per-request ContextVar；恢复既可能在启动期跑（ContextVar 空，正确），也可能被第一次查询**惰性**触发——那时 ContextVar 往往已被端点注入成板级子组 `vault:v:board`。**进程级** episode 缓存若按某一次请求的板级作用域装载并置 `_episodes_recovered=True`，其余白板的历史就**永久装不进来**。缓存是进程级的，作用域也必须是进程级的。
  - **为什么不是自己算好了当显式入参传**（初版做法，Codex round-1 HIGH-3 打回）：`_validate_scope_shape` 对**显式**传入的 `vault:default` 污染桶只告警放行。于是 active vault 没配置的进程会走成「查空桶 → 0 条 → `_episodes_recovered=True` → 永不重试」，把配置断裂伪装成"这个用户没有学习记录"——与本方法声称的 fail-closed 自相矛盾。
  - **空 Context 同时满足两者**：新 Context 没有任何 ContextVar 赋值 ⇒ 跳过"显式"分支、走 **active vault 派生**分支（方案甲要的进程级语义）；而派生分支对污染桶**抛** `VaultScopeUnresolved`（门 `test_unconfigured_active_vault_fails_closed_not_silent_empty` 锁死）。
- 作用域解析放在 `try` **之外**（`conversation_inheritance` 的 H-3 同型），并在 `except` 上加注释说明为何**不得**放宽成 `Exception`：`VaultScopeUnresolved` 刻意不继承 `RuntimeError`，放宽会把配置断裂伪装成"Neo4j 不可用 → 空历史"。
- **误路由旁路已钉测试**：`_run_query_json_fallback` 按关键词派发，`MATCH…LEARNED` 且无 `next_review` 的**三条**读（learning_history / all_recent_episodes / concept_history）中途降级时全部落到 `_handle_query_history`。门 7.6 用真实的 `_fallback_to_json` 路径（注入一个 session 即抛 `ServiceUnavailable` 的驱动）验证降级后结果仍在作用域内；门 7.7 + 单测验证无 scope 时 fail-closed **且**带 scope 时读得到（正向对照，防"恒空"假绿）。

**语义收窄如实声明**：`get_all_recent_episodes` 的 "all" 从「全库所有 vault」收窄为「本作用域族内（等值 OR 前缀）」。2026-08-30 现网 7691 只读实测：全库唯一 LEARNED 边落在 `vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d`（active vault 的 punycode 子组）⇒ 按 active vault 根组 + 前缀语义装载，**与收窄前的现网返回逐字节相同**。收窄是真的，只是现网当下无差异。

> **诚实边界**：上面这条"逐字节相同"只对**当前现网数据分布**成立，依据是 G4-1a 落盘的 7691 只读实测（本卡未重新连 7691 复测——硬边界要求只读，且该实证是一天前的同一套库）。若现网此后写入了别的 vault 的 LEARNED 边，恢复结果就会与收窄前不同（少装别的 vault），那是**预期内的修复**，不是回归。

### (d) 关联族三方法：只做契约收口 + 单测 ✅

`get_canvas_associations` / `get_canvas_concepts` / `find_common_concepts`（含 `load_all_canvas_associations`）是**双料僵尸**：`grep` 实证生产**零调用方**（唯一引用是 `load_all_canvas_associations` 自己调 `get_canvas_associations`，而它自己也无人调用），现网 7691 `Canvas`/`Node` 标签**零行**。

按卡文只做：
- Cypher 侧逐 alias 过滤片段断言（单测拦截真实发出的查询，**按 UNION 分段**逐段查）；
- JSON 镜像行为门（真实可见面：本 vault 根组 + 子组可见，他 vault 与近似前缀 vault 不可见）。

**不做**：不造 7692 行为门种子、不新增消费方。G-PIPE 处置（保留 / 退役）登记为 **G-PIPE-008**（`docs/known-gotchas.md`），另立卡——退役要连 `Canvas`/`ASSOCIATED_WITH` 的写侧一起看，超出读收口卡的范围。

### (e) 4 处 `@allow_cross_vault` 补挂 ✅

| 文件:函数 | reason |
|---|---|
| `app/api/v1/endpoints/health.py::_test_neo4j_connection` | connectivity ping (RETURN 1) — no business data read |
| `app/api/v1/endpoints/kg_health.py::kg_health_check` | system-wide KG health metrics / orphan sweep across all vaults |
| `app/api/v1/system.py::_check_neo4j` | connectivity ping (RETURN 1) — no business data read |
| `app/core/subject_config.py::list_subjects_from_neo4j` | bootstrap — list all user-created subjects across vaults |

> **口径差声明**：卡文写的是 `system.py:46`。仓库里有两个 `system.py`——`app/api/v1/endpoints/system.py` 只有 4 行注释（是个空壳，说明真正的端点在另一个文件），真正带 `RETURN 1` ping 的是 **`app/api/v1/system.py:46`**（`_check_neo4j`），与 `cypher_helpers.py:44` 既有清单所指一致。已按后者补挂。
> 装饰器标记**运行时实测**（不是"看着像挂上了"）：四个函数的 `._allow_cross_vault_reason` 均可读出预期字符串。

### (f) 裁判 ✅

见下节 §三。

### 收尾 ✅

- **Codex 审查存档**：`_bmad-output/审查/codex-review-CARD-G4-1b.md`（六轮全文 + 逐条整改记录 + 六轮小结）。round-6 终裁 **可合并**，BLOCKER/HIGH 清零。
- **契约文档**：`.claude/rules/cypher-read-contract.md` R4「未封堵存量」节**清零**并写入三条口径（名实一致 / 误路由旁路 / 进程级缓存不得按请求级作用域装载）。
- **G-PIPE 登记**：`docs/known-gotchas.md` 新增 **G-PIPE-008**（关联族三方法双料僵尸，处置另立卡）。
- **不 push**（硬边界）。

---

## 三、裁判结果

```
cd backend && caffeinate -i .venv/bin/pytest \
    tests/integration/test_cypher_contract_gate.py \
    tests/unit/test_neo4j_client.py \
    tests/unit/test_story_38_2_episode_recovery.py -q
```

| 套件 | 本卡前 | 本卡后 | 说明 |
|---|---|---|---|
| `test_cypher_contract_gate.py` | 49 passed | **63 passed** | 存量 49 全绿 + 门 7 新增 14 个用例（含门 7.8 生产形态端到端） |
| `test_neo4j_client.py` | 34 passed | **60 passed** | 新增 `TestG41bReadScopeContract` + `TestG41bMisrouteFieldParity`（26 个用例） |
| `test_story_38_2_episode_recovery.py` | **4 failed** / 8 passed | **16 passed** | 见下方"顺带修好的存量红" |
| 合计 | — | **139 passed** | |

**卡文之外、受本卡影响的两个测试文件**（mock 点适配，见 §四）：

| 套件 | 本卡后 |
|---|---|
| `test_story_38_7_ac1_fresh_startup.py` | 6 passed / 1 failed（**该 1 条在 HEAD 上就红**，与本卡无关） |
| `test_story_38_2_qa_supplement.py` | 17 passed |

**假绿防线**：`backend/scripts/g41b_mutation_negative_controls.py` —— 19 类机械变异，串行执行，还原后逐字节比对。

判据两次升级（Codex round-1 MEDIUM → round-2 Q6）：不再只看「整个文件有测试失败」，
而是解析 `-rf` 短摘要，**指定的那道门必须出现在失败清单里**；且匹配从**子串**收紧为
`::` 之后的**整段**比较（spec 带 `[...]` 时可精确指定参数化的某一条）。

round-3 再收紧一次：参数化门改用**完整 param id**（`test_g41b_concept_history_per_alias[g21gate_g41a_xc-False]`），
避免"兄弟参数化 case 失败也算命中"。

```
[baseline] 135 passed
[ch-json-simulator             ] RED ✅   [ch-and-not-or          ] RED ✅
[ch-drop-c                     ] RED ✅   [ch-drop-r              ] RED ✅
[episodes-unscoped             ] RED ✅   [episodes-json-unscoped ] RED ✅
[history-handler-warn-only     ] RED ✅   [history-handler-bound-parse-lenient] RED ✅
[history-handler-string-time-compare] RED ✅ [history-handler-drop-date-concept] RED ✅
[recovery-contextvar           ] RED ✅   [assoc-drop-target      ] RED ✅
[assoc-json-unscoped           ] RED ✅   [canvas-concepts-drop-n ] RED ✅
[canvas-concepts-json-unscoped ] RED ✅   [common-drop-c2         ] RED ✅
结果: 19/19 变异被杀 (门能红)
```

> **判据的残余上限（如实声明，不宣称已解决）**：粒度是「这条测试红了」，不是「红在我期望的那句断言上」。同一条测试里另一处断言先失败，依然算命中。再收紧要比对失败信息文本，会把门与断言措辞耦死，不做。

> **⚠️ 变异/自检当场抓到的三条判据缺陷（如实记录，全部已修）**：
>
> 1. **`canvas-concepts-drop-n` 首轮 GREEN（真死门）**。`get_canvas_concepts` 的 UNION **两个分支都有一个叫 `n` 的 alias**（分支1 = `Node`，分支2 = `LearningNode`）；判据是「查询文本里含 `read_group_filter('n')`」，删掉分支 1 的过滤后分支 2 的那份仍满足这个子串检查 —— **存在性断言的粒度与缺陷的粒度错位**。改为**按 UNION 分段逐段断言**（并断言分段数符合预期，结构一变立刻红）。
> 2. **grep 门把一条读查询静默当成了写**。写/读分类原本用裸子串 `"CREATE" in query.upper()`，而 `get_canvas_associations` 的 RETURN 里有 `r.created_at as created_at` —— `CREATED_AT` 含 `CREATE`，整条**读**查询被跳过检查，门却报 0 违规。改为词边界正则；并给门加了 `EXPECTED_READ_METHODS` 验伪锚：**实际检查到的方法集合**必须与清单逐字相等，不等即退出码 2。
> 3. **`ch-drop-c` 的「指定门」我写错了**。我把 recall/isolation 门列为期望红，但那条门的 fixture 把 concept 与 LEARNED 边放在同一个 group，丢掉 `c` 的过滤仍被 `r` 兜住 —— **结构上**就杀不掉单 alias 变异（门 6 的 H-4 教训）。升级后的脚本立刻报「未红的指定门」，判据自身被验伪了一次；已改指向逐 alias 门。
>
> 4. **门 7.6 名叫 misroute，测的却不是 misroute**（round-2 整改后由新变异 `history-handler-drop-date-concept` 抓出）。`_fallback_to_json()` 会把 `_use_json_fallback` 置 True **并关掉 driver**，所以**第一次**探针触发降级之后，后续调用走的是各方法自己的 `if self._use_json_fallback:` 分支（`_get_learning_history_json` —— 它本来就实现了 date/concept 过滤），**不再经过关键词误路由**。把 `_handle_query_history` 的 date/concept 过滤整个删掉，门仍然全绿。已加 `_rearm()`：每次探针前重置 `_use_json_fallback` 并重挂 boom driver。
> 5. **变异里的门名笔误**（`test_g41b_midflight_fallback_stays_scoped`，真名多一个 `_misroute_`）。子串匹配时代这种笔误会被「某处有失败」掩盖；换成整段比较后当场报「未红的指定门」。
>
> 6. **`canvas-concepts-json-unscoped` 的第二个期望门与它无关**（round-3 加严后抓出）。我按"多指一道门更强"的直觉给它加了 `test_mirror_path_match_is_exact_like_cypher[canvas_concepts]`，但那条门的两条 fixture 记录**都在作用域内**，去掉 group 过滤根本不改变它的结果。精确判据当场报「未红的指定门」——**加门不等于加强度，得看那道门是否依赖被变异的那段逻辑**。
>
> 六条同一个根：**「没有发生」不等于「验证通过」**。门首跑就该跑变异，并且要验判据自身的假阳/假阴（MEMORY `reference_gate_design_pitfalls` / `reference_mutation_script_catches_dead_gates`）。

**grep 门**（`neo4j_client.py` 无残留无 group 业务读）：见 §五复核命令，结果 0。

---

## 四、顺带修好的存量红（如实声明，非本卡引入）

`tests/unit/test_story_38_2_episode_recovery.py` 在**本卡改动前**就有 **4 个 failed**（用 `git show HEAD:` 还原双文件实测对照过，见 §五）：

```
TestEpisodeRecovery::test_recover_neo4j_unavailable
TestEpisodeRecovery::test_new_episodes_during_degradation
TestLazyRecovery::test_lazy_recovery_on_first_query
TestRecoveryIntegration::test_degraded_startup_then_lazy_recovery
```

**根因**：这 4 条用 `side_effect=Exception("Connection refused")` 模拟"Neo4j 不可用"，而生产的 `except` 是 `(RuntimeError, ConnectionError, asyncio.TimeoutError)` —— **裸 `Exception` 从来就不在捕获范围内**，异常直接穿透。也就是说 **Story 38.2 的 AC-3「Neo4j 不可用 → 优雅降级」从来没有被真正验证过**。

**处置**：把 fake 异常改成 `ConnectionError`（真实、且在捕获范围内），**不**放宽生产的 `except` —— 放宽会连 `VaultScopeUnresolved` 一起吞掉，正是本卡要防的静默降级。另外 4 处 fixture 的 `group_id: "math"`（Story 1.9 时代的裸 subject 组，与 vault 作用域不同族）改为当前作用域内的物理组。

**遗留观察（登记，不在本卡修）**：`get_all_recent_episodes` 若抛 `neo4j.exceptions.Neo4jError`（不继承 `RuntimeError`），恢复的 `except` 同样接不住，会从 `initialize()` 抛出去。这是既有形态、与跨库读无关，建议独立收债卡处理（放宽 except 需要单独论证不会误吞 `VaultScopeUnresolved`）。

### 更大范围的回归对照（HEAD 基线实测，不靠推断）

本卡改动触及 `neo4j_client` / `memory_service` 的公共方法签名，因此把**全部 18 个引用这些方法的测试文件**跑了一遍，再把**同一批 nodeid** 对着 `git show HEAD:` 还原出的源码跑一遍做对照（还原挂 `EXIT` trap，逐字节校验）：

| | 失败数 |
|---|---|
| 本卡改动下 | 67 |
| HEAD 源码下（同一批 nodeid） | 62 |
| **差集 = 本卡引入** | **5** |

5 条全部是 mock 点适配，已全部修复：

```
test_story_38_7_ac1_fresh_startup.py::...::test_memory_service_recovers_episodes_on_init
test_story_38_2_qa_supplement.py::TestCodeReviewFixes::test_recovery_limit_1000_passed_to_neo4j
test_story_38_2_qa_supplement.py::TestJsonFallbackEdgeCases::test_json_fallback_limit_one
test_story_38_2_qa_supplement.py::TestJsonFallbackEdgeCases::test_json_fallback_missing_fields_in_relationship
test_story_38_2_qa_supplement.py::TestJsonFallbackEdgeCases::test_json_fallback_none_timestamp_sorting
```

原因两类：(1) 恢复调用现在多带一个 `group_id=` 实参，`assert_awaited_once_with(limit=1000)` 需同步；(2) JSON 降级 fixture 的记录没有 `group_id`，而无归属记录现在一律不可见（与 Cypher 侧 `allow_null=False` 同口径）。修法是给 fixture 补归属、给断言补实参，**没有**放宽生产过滤。

> 剩下 62 条是 HEAD 上就红的存量债（e2e 批量端点、graphiti 双写、写重试族等），与本卡无关，不在本卡范围内修。

---

## 五、复核命令（一键）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v1-clientread/backend

# 主裁判（需 7692: docker compose --profile test up -d neo4j-test）
caffeinate -i .venv/bin/pytest tests/integration/test_cypher_contract_gate.py \
    tests/unit/test_neo4j_client.py tests/unit/test_story_38_2_episode_recovery.py -q   # 139 passed

# 假绿防线（19 类变异，串行，还原逐字节比对，指定门必须变红）
caffeinate -i .venv/bin/python scripts/g41b_mutation_negative_controls.py               # 19/19

# 读作用域 AST 门 — neo4j_client.py 无残留无 group 业务读（rc=0；并打印自身两个已知假阴面）
.venv/bin/python scripts/g41b_readscope_grep_gate.py

# 4 处 @allow_cross_vault 运行时实测
.venv/bin/python -c "
from app.api.v1.endpoints.health import _test_neo4j_connection as a
from app.api.v1.endpoints.kg_health import kg_health_check as b
from app.api.v1.system import _check_neo4j as c
from app.core.subject_config import list_subjects_from_neo4j as d
[print(f._allow_cross_vault_reason) for f in (a,b,c,d)]"

# lint
.venv/bin/python -m ruff check app/ scripts/g41b_mutation_negative_controls.py

# 存量红对照（证明 §四的 4 failed 不是本卡引入）
git show HEAD:backend/app/services/memory_service.py > /tmp/ms.head.py   # 双文件还原后跑同一套件
```

---

## 六、待用户裁决

| # | 事项 | 背景 | 建议 |
|---|---|---|---|
| 1 | **`/concepts/{id}/history` 开始返回数据，是否需要前端配套** | 该端点此前恒空。修好后凡是消费它的地方都会第一次看到真实 timeline。若前端对空 timeline 有特殊处理（如隐藏整块），可能需要看一眼 | 建议先上线观察一轮；本卡不动前端（DD-12 范围约束） |
| 2 | **关联族三方法（G-PIPE-008）保留还是退役** | 双料僵尸：零调用方 + 现网零数据。本卡只做契约收口，保留了它们 | 建议另立卡决定；退役要连写侧 `create_canvas_association` 一起看 |
| 3 | **`_recover_episodes_from_neo4j` 的 `Neo4jError` 穿透是否本批收** | §四遗留观察：驱动层异常不在捕获范围，会从 `initialize()` 抛出 | 建议独立收债卡（放宽 except 需论证不误吞 `VaultScopeUnresolved`） |
| 4 | **`get_canvas_concepts` UNION 第二支是否直接删除** | 该支的 `CONTAINS`/`LearningNode`/`HAS_CONCEPT` 全仓无写侧，7692 `EXPLAIN` 实测三者均"不存在"。本卡按 R1 给它的节点 alias 加了过滤，但它本质是死代码 | 建议随 G-PIPE-008 一并处置（删除属行为变更，不宜混进封堵卡） |
| 5 | **中途降级落 `else -> []` 的四类查询是否单立卡** | Codex round-1 HIGH-2 / round-2 Q3：`_run_query_json_fallback` 是**关键词路由**。`limit` 与 `startDate/endDate/concept` 本卡**已补齐**（三条 LEARNED 读降级前后条数与内容一致，门 7.6 + 变异 `history-handler-drop-date-concept` 锁）。**仍未处理**的是 associations / canvas concepts / common concepts / score history 四类查询中途降级直接落 `else -> []`——功能性假空，**不是**泄漏 | 建议独立收债卡：修它等于给 JSON 模拟器补四套查询解析，且要先定义「降级模式下这些接口应该返回什么」，超出读收口卡范围 |
| 7 | **`get_learning_history` 的 Cypher 日期过滤本身是坏的** | Codex round-3 Q3' 追出：写侧 `create_learning_relationship` 落的 `r.timestamp` 是 **temporal**（`datetime()`），而读侧把它与 `$startDate`（调用方 `datetime.isoformat()` 产出的**字符串**）直接比较 —— Neo4j 里 temporal 与 string 比较结果为 null，WHERE 不满足。本卡把**降级路径**修成了正确的时区感知比较（`_as_utc`），于是两条路径在**带日期过滤**时反而不等价：降级侧对、Cypher 侧错 | 建议独立收债卡（修它要动写侧类型或读侧参数类型，属 G2 写侧地盘；本卡铁律不碰写路径）。已在 `_handle_query_history` docstring 里点名，不留暗账 |
| 6 | **关联族镜像结构性死掉是否处置** | round-2 Q2 追出的事实：全仓唯一往 `self._data["relationships"]` 写记录的是 `_handle_merge_learning`，它写的键里**没有 `canvas_path`** ⇒ `_get_canvas_concepts_json_fallback` / `_find_common_concepts_json_fallback` 在真实数据上**恒返回空**。本卡按 R1 给它们做了作用域收口并如实写明「不宣称与 Cypher 语义等价」 | 建议随 G-PIPE-008 一并处置（与那三个零调用方的 Cypher 方法同族） |

---

## 七、独立对抗审计（2026-08-31，Codex 六轮之后追加）

Codex 六轮终裁「可合并」之后，又跑了一轮**互不知情的多视角审计**（6 维度并行找问题 → 每条发现 3 个不同棱镜的怀疑者试图证伪 → 完备性批评）。理由：六轮 Codex 审的是**我挑的问题面**；换一组不知道我关心什么的视角，才可能碰到我**没想到要问**的东西。

**结果：提出 26 条，证伪掉 10 条，存活 16 条。其中 1 条 HIGH 直接打在本卡的头号交付物上。**

### ⛔ HIGH：`get_concept_history` 的名实一致修复在**真实数据上是坏的**

- **实况**：写侧 `create_learning_relationship` 落的是 `SET r.timestamp = datetime()`——**temporal 值**；驱动 `result.data()` 不转换，`run_query` 返回 `neo4j.time.DateTime` 对象。而 `ConceptHistoryTimeline.timestamp: Optional[str]`，pydantic 直接 `ValidationError`，端点 `except Exception` → **HTTP 500**。
- **也就是说**：改动前该端点恒返回「200 + 空 timeline」，改动后**一旦作用域内真有数据就 500**。本卡的头号交付物（DD-13 名实一致）在真实数据上不成立，而 commit message、client docstring、以及已写进**常驻规则文件** `.claude/rules/cypher-read-contract.md` 的规范文本都把它记成已交付。
- **真库实测复现**（7692，生产形态种子 `datetime()` + 不设 `review_count`）：

  ```
  timestamp 的 python 类型: DateTime | neo4j.time.DateTime(2026, 8, 31, ...)
  响应模型: ⛔ ValidationError
    timeline.0.timestamp   | string_type | GOT: neo4j.time.DateTime(...)
    timeline.0.review_count| int_type    | GOT: None
  ```

- **为什么本卡 16 道门全绿却漏掉**：所有真库门的种子都写 `r.timestamp = $ts` 且 `$ts` 绑**字符串**，与生产写侧的 `datetime()` 形态不同。**fixture 形态 ≠ 生产形态**——与本卡**已经抓到**的「生产写侧从不落 `c.id`，所以只按 id 点查等于没修」是**同一类陷阱**，抓到了一次，却在同一张卡里漏了第二次。
- **修复**：客户端边界加 `_iso_timestamps()`（temporal → ISO 串，与相邻的 `desanitize_group_id_from_graphiti` 同属 R5「输出边界还原」），三条 LEARNED 读统一走它；service 的 `record.get("review_count", 0)` 改 `or 0`（`.get(k, d)` 只在**键缺失**时兜底，而 Cypher 对不存在的属性返回**键存在、值为 None**）。
- **补门 7.8**：用**生产形态**种子（temporal ts + 缺失 review_count，fixture 自证 `valueType(r.timestamp)` 含 `ZONED DATETIME`）走**真实 service 调用链**直到 `ConceptHistoryResponse(**result)`——即端点做的那一句。另加「三条 LEARNED 读的 timestamp 类型必须与 JSON 镜像一致」的类型对拍门。

### 其余存活项的处置

| 类别 | 条数 | 处置 |
|---|---|---|
| **降级落点丢字段** | 1 | `_handle_query_history` 原先**不返回 `group_id`**，而 `get_all_recent_episodes` 中途降级正落在它上面 → 恢复进**进程级** episode 缓存的记录带空归属，之后每次 `group_in_read_scope` 判定都是 False、永久不可见，且 `_episodes_recovered=True` 不会再恢复。已补 `group_id` + `agent_type`，与镜像逐字同型；配两道单测（字段集一致 + 恢复的 episode 作用域判定为 True）与变异 `misroute-drops-group-id` |
| **grep 门两处假阴** | 2 | 方法级 `has_filter` 会放行「已有过滤的方法里再加一条无过滤读」；含写关键字的读查询被整条跳过且不计入自检清单。**不假装修好**——改成把两个假阴面**逐条打印**（`ℹ️` 行）并在 docstring 写明本门的定位是「方法级粗筛 + 清单锁」，逐查询的证明归门 7 的逐 alias 行为门 |
| **文档不实** | 8 | 见下 |
| **既有/越界** | 4 | `get_review_suggestions` 的同类型边界（既有方法，同一 `_iso_timestamps` 已覆盖 timestamp 侧，`concept_id` 恒 null 属写侧问题）、recovery 的 `VaultScopeUnresolved` 传播路径（§六 #3 已登记）等，均已在 §六 待裁决表内或属存量债 |

### 文档不实 8 处（全是同一个病：声明比证据宽）

最严重的一条：**常驻规则文件 `.claude/rules/cypher-read-contract.md` 把「被 Codex round-1 打回的初版做法」（`default_vault_group_id()` 当显式入参）记成了 G4-1b 的正式口径**——与实际代码（空 `contextvars.Context()` 走派生分支）相反。规则文件是后人照抄的模板，写错等于把缺陷复制到下一张卡。已更正，并把「别写成显式传参」连同原因写进条文。

其余：整改记录声称「docstring + 契约文档 + 验收单三处都改成快照结论」而实际只改了 1 处；§五 复核命令的期望值是陈旧数字（`128 passed` / `12/12`）；那条 `grep -c "MATCH (u:User)..."` **实测返回 2 而文档标 0**，且它根本不检验注释里说的那件事（已换成 AST 门）；用户可感表的「两条路径同一套可见面」与本卡自己的 docstring 明文否定冲突；`known-gotchas.md` 的**合计行**未随 G-PIPE 7→8 更新。

### ⚠️ 本轮审计自身的覆盖缺口（如实声明）

审计的 85 个 agent 里 **14 个因周额度上限失败**，全部落在 `gates` 维度的证伪棱镜与**完备性批评**上。因此：
- `gates` 维度的 2 条发现只有 **1 票**支持（其余棱镜没跑成），证伪强度低于其他维度的 3 票；
- **完备性批评（「什么没被检查到」）根本没跑成**——本轮审计**没有**回答「这 6 个视角本身的盲区是什么」。

这不是「审计通过」，是「审计跑到一半额度用尽」。若要补，重跑 `Workflow({scriptPath: ..., resumeFromRunId: 'wf_cb8af748-a8b'})` 即可命中缓存续跑。

### 这一轮真正的教训

**门首跑就该跑变异——而且要看它红在哪条断言上。** 本轮修复过程中，变异脚本又当场抓出**两条我自己新写的错**：

1. `misroute-drops-group-id` 判 GREEN——我的**变异**写错了：在 dict 字面量里**前插**同名键，而 Python dict 重复键**后者胜**，等于空操作。
2. `review-count-none-not-defaulted` 判 GREEN——我的**门**写错了，而且是更严重的一种：我在测试里把 `memory_service` 的 timeline 构造「**逐字复刻**」了一遍（注释还是我自己写的），于是这道门**从不执行**它声称保护的那段生产代码。改坏 service，门照样绿。已改成调**真实 service 调用链**。

复刻逻辑 ≠ 测试逻辑。门必须走真实链路。
