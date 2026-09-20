# 独立复核请求 — CARD-LANCE-INDEX-DELETE-CONTRACT

## ① 背景与最小读取面

仓库根: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage`
（git worktree，分支 `card/p1-storage`）。你是**只读**复核者，不要修改任何文件、不要连任何数据库。

本次改动的完整范围：

```
git --no-pager diff --no-color 5e0f87b7efc2c08693902dd470d9764974b90b67 3c45f9ad -- . ':(exclude)_bmad-output'
```

（`5e0f87b7…` = 本车道上一张卡 CARD-LANCE-DUALWRITE-NEVER-WRITES 的末 commit，本次改动的基线；
`3c45f9ad` = 本卡末 commit，也是当前 HEAD。）

本卡共 5 个 commit：
`db9bf6d1` 代码与门 → `bbb72916` 把 `backend/openapi.json` 还原到 PREV 态
（lefthook `spec-sync-flat` 会把再生的快照顺带塞进代码 commit，快照由主 session 集成期统一再生）
→ `d6b7fa42` 补 `listing_failed` 门 → `2e331c49` 修 `add_documents` 单快照缺陷 + 回归锁
→ `3c45f9ad` 把 P1-A 的分页外追加门按其自身指令翻正。

除该 diff 外，请只读下列文件的下列范围（不要通读全仓）：

- `backend/lib/agentic_rag/clients/lancedb_client.py`
  - `_vault_ids_from_fingerprint_tables` 与 `_canonical_logical_tables` 全段（改前 :984-1049，改后按符号名定位）
  - `drop_vault_tables` → `drop_vault_tables_report` → `_drop_vault_tables_pinned` 全段（改前 :1325-1457）
  - `_cache_tables` 全段（改前 :1529-1588）
  - `add_documents` 的建表分支附近（改前 :4405-4432）
  - `_ensure_vault_fingerprint_table`（本卡新增）与 `_update_fingerprint`、`_fingerprint_table_exists`、`_fingerprint_table_name`
  - 归属规则 `_owns_table` / `_table_owner` / `_scope_depends_on_registry`（本卡**声明零改动**，供你核对这条声明）
- `backend/app/api/v1/endpoints/index.py` 的 `delete_vault_index` 全段
- `backend/tests/unit/test_index_delete_contract_c101.py` 全文（本卡新增）
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 的「门⑨ 族」新增段（文件末尾）
- `backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py` 的 Test 10（DELETE 段）
- `backend/tests/unit/test_edge_rationale_fallback.py` 的
  `test_lancedb_real_write_appends_beyond_default_pagination`（本卡翻正的那条，见 ② 第 12 点）
- 裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §二 T1-A 行（:136）
- 前序复核存档 `_bmad-output/审查/codex-review-CARD-G2-9-F2-r7.md` :19-33（HIGH / MEDIUM 原文）
  与 `codex-review-CARD-G2-9-F2-r5.md` 的 M1 / M2 条目

改前的问题：`DELETE /index/{vault_id}` 只看 `drop_vault_tables` 的 `int` 返回值，而四道整次拒绝闸
全部 `return 0`，「名下没有表」是 `0`，「每一张都删失败」也是 `0` —— 三者共用同一个
`404 No tables found`；部分失败回 `200` 且不带失败清单。

## ② 作者自述（请独立核对，不要采信）

1. **五态互斥且完备**：`DropVaultReport.outcome` ∈ `{no_tables, refused, dropped, partial, all_failed}`，
   判定顺序为 refusal_kind → attempted 空 → failures 空 → dropped 空 → 其余。作者主张这五支两两互斥、
   并集覆盖全部可达状态。
2. **`int` 契约与既有诊断字段语义零变化**：`drop_vault_tables(vault_id) -> int` 仍返回**实删数**；
   `_last_drop_failures`（`(表名, "ExcType: 原文")`）与 `_last_drop_refusal`（完整文案）格式与内容
   与改前逐字相同。
3. **四道闸一道都没放宽**：闸序与判据不变，只是把 `return 0` 换成填 `refusal_kind` 后返回回执。
4. **响应体脱敏**：409 / 500 / 207 的体只含表名、`refusal_kind`、`error_type`；异常原文与完整
   refusal 文案只进 `logger`。作者主张体内不可能出现库路径或异常 message。
5. **(e1) 对 default / 裸表口径是 no-op**：`_ensure_vault_fingerprint_table` 只在
   `_scope_depends_on_registry(active)` 为真时动作。
6. **(e2) 形态核的不对称原则**：候选指纹表**打不开**时**保留**候选（宁可多认，误报方向只是少认领
   自己的表，不丢数据）；明确不是指纹形态（有 `vector` 列 / 缺列）才排除。
7. **(e3)**：`self._db.table_names()` 的裸调用在 `lancedb_client.py` 里归零（`_all_table_names`
   本体内的那次带 `limit=10_000` 的调用除外）。
8. **`refusal_kind` 的可达面**：作者主张 `listing_failed`（闸②）在 **scoped vault 上打不到** ——
   同一次枚举失败会先让 `_known_vault_ids` 置 `_vault_registry_degraded`，闸①抢先拒绝；它只在
   **裸表口径**（`default` / 空 vault，闸①对其整个跳过）可达。
   门：`test_listing_failed_409_and_is_only_reachable_for_bare_scope`。请核这条推理是否成立，
   以及有没有别的输入能在 scoped vault 上走到闸②。
9. **形态核的代价**：`_looks_like_fingerprint_table` 对每个以 `_file_fingerprints` 结尾的候选做一次
   `open_table` + 读 schema。作者的主张是「候选数 = vault 数，不是表数」，而
   `_known_vault_ids(force_refresh=True)` 在每次破坏性操作（删索引 / 启动自愈）时各跑一次。
   请核这个代价评估是否成立，以及在库很大时它会不会变成启动路径上的新瓶颈。
10. **本卡自己引入又修掉的一个缺陷**（请独立核对修法与门是否够）：(e3) 把 `add_documents` 里
   两次 `table_names()` 枚举合并成一次快照后，夹在两次之间的
   `_check_and_fix_dimension_mismatch` 会 `drop_table`，于是旧快照让代码去 `open_table` 一张
   已删的表 ⇒ 异常被外层 `except` 吞成 `return 0` ⇒ 写入静默全丢。
   修法 = 接住该守卫的返回值；锁 = `g29f1::test_add_documents_recreates_table_dropped_by_drift_guard`。
   **请特别检查**：`lancedb_client.py` 里还有没有同族形态（两次读取之间夹着会改变被读状态的调用），
   以及这条门的断言是否足够（它断的是**行数**，不只是"表还在"）。
11. **M2 的终态**：`LANCEDB_INDEX_TABLE_NAME` 撞指纹后缀时，作者**没有**让 vault 变得能删索引 ——
   伪 vault 不再被造出来（闸③不再误拒），但那张表随后被闸④当模糊名整次拒绝（409 +
   `ambiguous_tables`）。这是卡文明写并接受的结果：把它定性为**配置错误**并让它响。
   请核这个取舍在代码里是否被如实地实现与记录（而不是被描述成"修好了"）。
12. **翻正了一条 P1-A 留下的占位门**：`test_edge_rationale_fallback.py` 里原有
   `test_lancedb_real_write_second_append_beyond_pagination_fails_loudly` —— 它钉的是
   「上游 `add_documents` 用默认分页判存在性 ⇒ 分页外的第二次追加会**响亮失败**」，
   并在失败消息里写明「若哪天它真的成功了，说明上游已修，请删掉本门并把 G1② 的
   append-only 覆盖到分页外场景」。本卡 (e3) 修掉了那条上游限制，于是按它的指令翻正为
   `test_lancedb_real_write_appends_beyond_default_pagination`（同一条 edge ⇒ 2 行）。
   **请核**：翻正后的判据是否真的覆盖了「分页外」这个面（两条前提断言够不够），
   以及有没有因此丢掉原门守住的某个性质（例如「第一条不被静默毁掉」）。

## ③ 请按重要性排序回答的问题

0. **(e1) 是否真把 r7 场景的两条路径都关掉了**：drop 侧与自愈侧（`_cache_tables`）是否都因为
   「V 被指纹表补全」而不再认领长 id vault 的表？有没有哪条路径在指纹表**建成之前**就会跑到？
1. **形态核会不会把真指纹表误排**：空表、旧 schema 少列、列名大小写/类型不同的真指纹表会怎样？
   误排的后果是该 vault 从 V 里消失 ⇒ 它的表被短 id vault 认领 ⇒ **丢数据**。这是漏报方向，
   请特别检查。
2. **207 / 500 / 409 的体是否泄漏路径或凭据**：请指出你能想到的会让异常 message 进入响应体的
   输入，指出未被拦下的输入。
3. **`add_documents` 建表分支加钩子之后**：建指纹表抛错时，内容表的写入结果是否会被伪装成
   成功或失败？返回值语义有没有变？
4. **`test_wave5_...` 三条用例的改写**：是不是只是「让 mock 迎合新代码」而没有证到任何契约？
   （作者的立场是真契约门在 `test_index_delete_contract_c101.py`，wave5 那三条只维持
   ContextVar 注入与 503 两条既有断言。）
5. **pyright 0 是否靠 `# pyright: ignore` 掩盖**：请指出每一处 ignore 及其理由是否成立。
6. 门本身：`test_index_delete_contract_c101.py` 与 g29f1 门⑨ 族里，哪些断言是**门未覆盖的路径**，
   哪些断言会在实现被改坏时**仍然通过**（请给出具体的对照输入）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条：

```
[级别] <一句话结论>
file:line
复现思路: <一句话>
```

用词请用「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」这类表述。

## ⑤ 边界

- **只读**。不要修改文件，不要运行会写入的命令，不要连 Neo4j（7691/7687/7692）或任何网络服务。
- **不在本卡范围**（看到了也请归到 LOW 或直接跳过）：
  - P1-A 的 `edges.py` / `neo4j_client.py` 双写面；
  - P1-C 的 `memory_service.py` / `episode_worker.py` / `group_id_compat.py` 组族 builder；
  - r5-M1 的**放宽**（本卡只暴露不放宽，放宽需要经确认的归属清单或表级元数据）；
  - `_pinned_vault_ids` 的嵌套问题（r5-LOW，已登记钉住）；
  - `backend/openapi.json` 未再生（由主 session 集成期做）；
  - 改前已存在的、无指纹表的存量 vault（D-41 用户授权项，本卡不追溯）。
