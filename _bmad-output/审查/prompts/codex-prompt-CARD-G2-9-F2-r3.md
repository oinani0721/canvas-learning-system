# 复核请求 — CARD-G2-9-F2（LanceDB 最长前缀优先归属）round-3

你是独立复核者。请只读、不改任何文件、不连任何数据库或网络服务。

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance`
（git 分支 `card/t1-lance`；本次审查绑定 `08100483..8583c6b2`，`08100483` 是批次基线 B14_BASE。
**round-1 提 4 HIGH、round-2 提 3 HIGH，作者已逐条整改；本轮请核 round-2 三条 HIGH 是否闭合、整改本身有没有引入新问题。**）

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

1. `git --no-pager diff 08100483 8583c6b2 -- . ':(exclude)_bmad-output'` —— 本卡全部改动；
   （只看本轮整改增量：`git --no-pager diff ab249816 8583c6b2 -- . ':(exclude)_bmad-output'`）
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

## ②bis round-2 三条 HIGH 的处置（请逐条核对是否真的闭合）

- **r2-HIGH-3（短 vault 丢失自己的指纹归属 ⇒ 删内容后增量索引判 unchanged）**：作者
  **接受这是本卡引入的新回归**。处置 = `drop_vault_tables` 前置闸：本 vault 的规范指纹名
  `{vault_id}_file_fingerprints` 若存在却按最长前缀归了别人 ⇒ **整次拒绝**（返回 0，
  `_last_drop_refusal` 记原因 + `logger.error`），一张表都不删。门
  `test_drop_refuses_when_fingerprint_would_be_orphaned`（a_file 只是个空 vault 即可触发）。
  请核：拒绝闸的判定用的是「规范指纹名」还是「实际归属集合」，有没有别的表也会被拆开
  （例如内容表之间、或别的按 vault 前缀命名的基线类表）？整次拒绝会不会让某些正当的
  删索引永远做不成、且没有出路？
- **r2-HIGH-1（目录缺项不设降级 / 降级标志无人消费）**：处置 = 按你建议的局部闭合 ——
  来源**明确失败**时（根目录不是目录 / 枚举抛错）置 `_vault_registry_degraded` 并在
  `drop_vault_tables` 整次拒绝。门 `test_drop_refuses_when_vault_registry_is_degraded`。
  **未闭合部分作者如实登记**：单个 vault 目录被移走/隐藏/失去 `.obsidian/` 时扫描不报错、
  不置降级，该 vault 若又没有指纹表，其表仍会被 id 更短的 vault 认领 —— 与本卡改前同态
  （不是回归），作者的判断是"这是来源②的定义域边界，闭合它需要额外归属证据"，已写进
  验收单「本卡未证明什么」并移交。请核这个判断是否成立，以及你是否看到成本可接受的闭合法
  （注意：把删除面限制成"只删已知逻辑表名"会打红既有门③ 的正向对照）。
- **r2-HIGH-2（TTL 沿用已失效的缺项集合）**：处置 = **降级结果一律不缓存**（连同
  `_db is None` 那条），降级期间每次判定重扫目录。门
  `test_known_vault_ids_cache_does_not_outlive_the_connection` 覆盖未连库那条。
  请核：还有没有别的"缺项但不降级"的结果会被缓存并在 TTL 内造成同类后果？
- **r2-MEDIUM-4（两处分页验证未覆盖失效态）**：page-outer 填充表 10 → **12**，使本 vault
  自己的 `a_10`/`a_11` 落到默认分页之外（退回十张枚举时 `own_left` 当场非空）；指纹分页
  另立门⑨ `test_fingerprint_baseline_readable_beyond_default_page`（**不删任何表**，只把
  指纹表挤出首页）。请核这两处现在是否真能被对应的退化变异打红。
- **r2-MEDIUM（loguru 下 %s 不插值）**：本卡新增的 5 处日志改 f-string。请核有无遗漏，
  以及是否有新增日志在 loguru 缺席分支下反而出问题。
- **r2-MEDIUM-7 / r2-LOW**：接受并登记。judge 1 那条字面 grep 作者**不改写拼法规避**，
  如实报「未达成，实测 1」，另出 AST 替代判据（`_owns_table` 经 `_table_owner` 得结论 +
  `_has_vault_prefix` 的调用方恰为 `{_table_owner, resolve_table_name}`，自带验伪锚），
  交主 session 裁定。

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
