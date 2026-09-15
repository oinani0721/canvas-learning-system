# 复核请求 — CARD-G2-9-F2（LanceDB 最长前缀优先归属）round-6

你是独立复核者。请只读、不改任何文件、不连任何数据库或网络服务。

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance`
（git 分支 `card/t1-lance`；本次审查绑定 `08100483..675bfd70`，`08100483` 是批次基线 B14_BASE。
**这是第 6 轮 —— 主 session 2026-09-14 在轮次上限之外**专为你 round-5 的 HIGH-1 **额外授权的一轮**。
本轮改动**只有一处**（`_cache_tables` 的选表条件 + 一条新门），请优先核它；其余部分与 r5 所审一致。 round-4 你提了 3 HIGH（H1 目录局部失效的缺项 V / H2 启动自愈不检查降级 / H3 TTL 在流程中段重算）+ 3 MEDIUM + 1 LOW，作者已逐条整改。请核这些是否闭合，以及整改本身有没有引入新问题。⚠️ 若仍有 HIGH，请明确指出**它是不是本卡引入的回归**，还是与改前同态的既有边界 —— 后者作者会登记移交而不在本卡强行闭合。）

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

1. `git --no-pager diff 08100483 675bfd70 -- . ':(exclude)_bmad-output'` —— 本卡全部改动；
   （**只看本轮增量**：`git --no-pager diff 647ef77f 675bfd70 -- . ':(exclude)_bmad-output'` —— 只有 56 行）
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

## ②bis round-5 的处置（本轮唯一改动）

- **r5-HIGH-1（启动自愈仍会误删长 vault 的漂移表）**：**接受并修**。你指出 r4 的模糊表名
  拒绝闸只加在 `drop_vault_tables`，`_cache_tables` 没有 —— 作者复核认同这是**本卡修复
  自身的覆盖不对称**，不是定义域极限。本轮把同一条判据（余名还含下划线、又不是
  `_canonical_logical_tables()` 里的任何逻辑名 ⇒ 不进维度修复）加到自愈选表上，
  句柄照常装载（读侧不受影响）。
  门：`test_cache_tables_skips_tables_whose_owner_cannot_be_determined`，含正向对照
  （本 vault 自己、余名为规范逻辑名的漂移表仍被自愈）+ `_vault_registry_degraded is False`
  的排他断言（防被降级闸挡住而假绿）。负控 NC18（去掉该条件）已实测转红。
  请核：① 这条闸加到自愈侧后，有没有把**正当**的自愈也挡掉（例如本 vault 真实存在、
  但表名不是逻辑名的历史表 —— 后果是它永远修不了维度）？② 自愈侧还有没有别的入口能从它下面走掉？③ 与 drop 侧那条是否真的同口径（不要求代码复用，但语义须一致）？

- **r5-HIGH-2（余名恰好是内置逻辑名时可穿过该闸）**：作者判为**真·定义域边界**，
  **本卡不修**，理由：此时表名在两种合法解释下都成立（vault `a` 的 `canvas_nodes`
  vs vault `a_canvas` 的 `nodes`），表名启发式给不出正确答案，闭合需要**表级归属元数据**
  （写表时落 `owner_vault`），属设计级改动。与你的归类「基线既有边界」一致，已登记移交。
  若你认为存在成本可接受的闭合法，请写明。

- **r5-M1（历史逻辑名）/ r5-M2（配置名以 `_file_fingerprints` 结尾造出伪 vault）/
  r5-LOW（钉住不支持嵌套）**：登记，建议第十五批立卡，本轮**未修**（本轮只修 HIGH-1）。

- **r5-M（API 把拒绝/全失败/无表混成 404）**：消费端移交，本卡禁改 `backend/app`。

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
