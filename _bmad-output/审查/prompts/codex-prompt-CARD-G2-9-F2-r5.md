# 复核请求 — CARD-G2-9-F2（LanceDB 最长前缀优先归属）round-5

你是独立复核者。请只读、不改任何文件、不连任何数据库或网络服务。

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance`
（git 分支 `card/t1-lance`；本次审查绑定 `08100483..647ef77f`，`08100483` 是批次基线 B14_BASE。
**这是第 5 轮，也是本卡轮次上限。** round-4 你提了 3 HIGH（H1 目录局部失效的缺项 V / H2 启动自愈不检查降级 / H3 TTL 在流程中段重算）+ 3 MEDIUM + 1 LOW，作者已逐条整改。请核这些是否闭合，以及整改本身有没有引入新问题。⚠️ 若仍有 HIGH，请明确指出**它是不是本卡引入的回归**，还是与改前同态的既有边界 —— 后者作者会登记移交而不在本卡强行闭合。）

**缺陷（数据丢失面）**：`LanceDBClient` 判断"一张表属于哪个 vault"时只看"表名是否以
`{vault_id}_` 开头"。于是 **id 较短的 vault 会单向认领 id 较长的 vault 的表** ——
`a_b_canvas_nodes` 以 `a_` 开头，所以 vault `a` 的启动自愈（`_cache_tables` →
`_check_and_fix_dimension_mismatch`）与显式删索引（`DELETE /index/{vault_id}` →
`drop_vault_tables`）都会删掉 vault `a_b` 的表。本仓可达：`app.config.sanitize_vault_id`
产出的 id 含下划线（`cs 61b` → `cs_61b`），vault `cs` 与 vault `cs_61b` 并存即触发。
前一张卡（CARD-G2-9-F1）已把归属规则收成单点 `_owns_table`，但没改这个口径，并把它的
可达面从"默认分页前 10 张表"扩大到了全库；本卡（F2）改的就是这个口径。

**本卡的改法**：归属改为**最长前缀优先** —— 表 `t` 归 vault `vid`，当且仅当 `vid` 是
**已知 vault 集合 V** 中使 `t == v` 或 `t.startswith(v + "_")` 成立的**最长**那个 `v`。
V 有三条来源（`_known_vault_ids`）：`VAULTS_ROOT` 目录枚举（主来源）、active vault
恒并入、以及从库内 `X_file_fingerprints` 形态的表名反推出的 X。

**最小读取面**（不需要读别的文件）：

1. `git --no-pager diff 08100483 647ef77f -- . ':(exclude)_bmad-output'` —— 本卡全部改动；
   （只看本轮整改增量：`git --no-pager diff 04eec9e9 647ef77f -- . ':(exclude)_bmad-output'`）
2. `backend/lib/agentic_rag/clients/lancedb_client.py` 的这几段（行号以当前 HEAD 为准，
   建议用 `grep -n 'def <名>'` 现场重锚）：`resolve_table_name` / `_vault_id_for_dir` /
   `_discover_vault_ids_from_root` / `_vault_ids_from_fingerprint_tables` /
   `_known_vault_ids` / `_table_owner` / `_warn_namespace_collision` / `_owns_table` /
   `list_vault_tables` / `drop_vault_tables` / `_cache_tables` / `_fingerprint_table_name`；
3. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文；
4. 参考（只读）：`backend/app/api/v1/endpoints/vault.py` 的 `list_vaults`、
   `backend/app/api/v1/endpoints/review_overview.py` 的 `_list_vault_dirs`
   （本卡的 vault 候选规则逐字沿用这两处）、`backend/app/config.py` 的
   `Settings.vault_id` 与 `sanitize_vault_id`、`backend/app/api/v1/endpoints/index.py`
   的 `delete_vault_index`（`drop_vault_tables` 返回值的消费方）。

## ② 作者自述 —— 请独立核对，不要采信

1. 最长前缀规则在 V = {`a`, `a_b`} 上给出：`_owns_table("a_b_canvas_nodes", "a")` 为假、
   `_owns_table("a_b_canvas_nodes", "a_b")` 为真、`_owns_table("a_canvas_nodes", "a")` 为真。
2. **被问的那个 vault_id 恒并入候选集**（不是只用 V）。作者的主张是：因此规则的最弱形态
   等于改前的口径，本卡**只减少"认领别人的表"，不减少任何 vault 对自己表的认领**。
3. V 的完整性是这条防线本身；V 里缺哪个 vault，那个 vault 的表就会被 id 更短的 vault
   重新认领。作者主张已用负控②（把 V 打成只含 active vault）证明门会红。
4. `_owns_table` 的哨兵三态未被改坏：不传 = active vault；显式 `None`/`""`/`"default"`
   = 裸表口径（`"_" not in name or name == FINGERPRINT_TABLE`）；显式 vault = 该 vault。
5. `_fingerprint_table_name` 与 `resolve_table_name` 是拼接侧，作者给它们加了"拼出来的
   名字按同一条规则是否判回自己"的自检，不自洽时 `logger.error` 但**不改名**。
6. `drop_vault_tables` 由"返回尝试数 + `except: pass`"改为"返回实删数 + 失败进
   `_last_drop_failures` + `logger.error`"，返回类型仍是 `int`。
7. V 的计算带 5 秒单调钟 TTL 缓存，作者主张：不缓存会按表重算而拖垮启动路径；
   缓存不设上限会陈旧到让新 vault 的表重新被认领；5 秒够是因为"vault 刚出现且已经有表"
   在物理上不可能（建表要先跑完索引）。

## ②bis round-4 各条的处置（请逐条核对是否真的闭合）

- **r4-H3（TTL 在流程中段重算出缺项 V）**：新增 `_pinned_vault_ids()` 上下文管理器 ——
  破坏性操作入口 `force_refresh` 之后把集合**钉住**，整个操作期间 `_known_vault_ids()`
  直接返回钉住值，`finally` 解钉。`drop_vault_tables` 与 `_cache_tables` 两条路径都钉。
  门两条：`test_pinned_vault_ids_freezes_the_registry`（机制面；⚠️ **初版是空门** ——
  拿掉钉住查询后它落到刚 force_refresh 装进去的 TTL 缓存、照样返回同一集合，负控当场抓到；
  现已在窗口内把 `_known_vaults_cached_at` 打成过期再问）与
  `test_drop_runs_under_a_pinned_registry`（行为面：在每次真实 `drop_table` 发生时记录
  钉住状态）。请核钉住有没有泄漏路径（异常、嵌套、并发/重入），以及两条门是否真能红。
- **r4-H1（目录局部失效 ⇒ 不降级的缺项 V）**：作者**没有**声称能把 V 补全，而是从
  **表名**这一侧加了一道拒绝：删除集合里若出现「余名里还含下划线、又不是本客户端会拼出的
  任何逻辑名」的表（如 `a_b_canvas_nodes` 对 vault `a` 的余名是 `b_canvas_nodes`），
  整次拒绝。门 `test_drop_refuses_tables_whose_owner_cannot_be_determined`。
  请核：① 这条判据会不会把**正当**的删除也拒掉（本 vault 真实存在、但名字不是逻辑名的表）？
  ② 会不会被绕开（某个长 id vault 的表余名恰好是一个逻辑名）？③ 它是否真的覆盖了你 r4-H1
  复现思路里的那条路径？
- **r4-H2（启动自愈不检查降级）**：降级时**跳过维度修复**，表句柄照常装载（读侧不受影响）。
  门 `test_cache_tables_skips_healing_when_registry_is_degraded`。
- **r4-M1（三个规范表名不是闭集）**：改走 `_canonical_logical_tables()`，把
  `LANCEDB_INDEX_TABLE_NAME` 配置值并进来（你给的链路 `config.py:508` →
  `lancedb_index_service.py:477` → `index_canvas` 已核实）。配置取不到时只回内置集 ——
  只会更保守（更容易拒绝），不会放行。请核还有没有别的路径能拼出 vault 前缀表名。
- **r4-M2（降级不缓存无门）**：补 `test_degraded_registry_result_is_not_cached`
  （不走 force_refresh，只看普通查询：先降级、再恢复来源、立刻再问）。
- **r4-L1（TTL 常量旁的论证已被推翻）**：已改写为「破坏性路径钉住 + 强制重算；TTL 只服务
  读侧/命名侧高频调用」。
- **r4-M3（API 把拒绝/全失败/无表混成 404）**：移交登记，不在本卡改 `backend/app`。

## ③ 请回答的问题（按重要性排序）

⓪ **V 的完整性**：有没有哪条路径会让某个真实存在的 vault 不进 V，从而让归属退化回
   改前口径、缺陷复活？三条来源各自的失效形态（目录被移走、`VAULTS_ROOT` 不可达、
   vault 用 `.canvas-config.yaml` 声明了与目录名不同的 id、vault 一张表都还没有）
   分别会落到哪一侧？作者说"误报方向是少认领、不丢数据"，这个不对称成立吗？
   TTL 缓存的陈旧窗口有没有作者没想到的到达方式？

① **default / 空前缀**：`vid` 为空或 `"default"` 时走裸表分支。新规则有没有可能让
   default 退化成"全表可见"或"恒空"？`_table_owner` 里对 `v == "default"` 的跳过
   会不会在某个组合下让一张表变成无人认领（进而永远删不掉）？

② **`resolve_table_name` 的回归面**：幂等守卫从"以我的前缀开头"改成"按新规则归我"。
   对**存量已建表**（改前按朴素前缀命名的表）会不会产生双前缀（`a_a_b_...`）或漏前缀？
   生产调用点传进来的都是逻辑表名吗，有没有传已解析名的路径？

③ **门的覆盖**：新增的互前缀门与 drop 记账门读回表名时有没有走到**门未覆盖的路径**
   （例如默认分页只看前 10 张表的那条）？正向对照（自己的漂移表仍被处理）是否真的证明
   了隔离，而不是别的原因导致表消失/保留？

④ **判据的可证伪性**：三段负控输入（退回朴素前缀 / V 打空 / drop 记账改回吞掉）各自
   让哪条断言变红？作者主张这三段的红点互相可区分 —— 成立吗？有没有哪段其实是被
   另一条断言先拦下的（即该负控并没有测到它声称测的那一层）？

⑤ **`drop_vault_tables` 契约**：返回值语义由"尝试数"变"实删数"，全部删失败时返回 0 会
   让 `DELETE /index/{vault_id}` 从 200 变 404。除 `endpoints/index.py` 与
   `backend/scripts/g29_dual_vault_canary.py` 外还有别的消费方吗？这个变化有没有副作用？

## ④ 输出格式

逐条列出发现，每条写成：

```
[BLOCKER|HIGH|MEDIUM|LOW] <一句话结论>
  file:line  <定位>
  复现思路：<一句话说明怎样观察到它>
```

没有发现就明确写"该级别无"。请不要改写文件，也不要给出补丁。

## ⑤ 边界

- 只读：不修改任何文件，不执行写操作，不连接 Neo4j / LanceDB 现网目录 / 任何网络服务。
- 不评：完整 canary 复跑（那是下一张卡 CARD-G2-9-F1-canary 的范围）、
  `_check_and_fix_dimension_mismatch` 内部的 drop 条件设计、以及 `backend/app` 下与本卡
  改动无关的既有问题。
- 本卡地盘只有两个文件（`lancedb_client.py` 与 `test_lancedb_cross_vault_drop_g29f1.py`）；
  若你认为修复需要动这两个之外的文件，请写成 MEDIUM/LOW 的移交建议，不要当成本卡缺陷。
