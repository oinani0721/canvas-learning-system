# UAT — CARD-LANCE-INDEX-DELETE-CONTRACT

> 批次: `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage`（分支 `card/p1-storage`）· 本车道第 **2/4** 张
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P1-B.md`（feature 主干树）
> `PREV`（P1-A 末 commit）: `5e0f87b7efc2c08693902dd470d9764974b90b67` — `_bmad-output/审查/evidence-lance-index-delete/prev-sha.txt`
> 最终代码 SHA: `f6ea5006` · 本卡 commit 总数: **10**（含 docs 收尾 `c51c3962`）· Codex 轮次: **3 轮 + 第 4 轮受阻**
>
> ## ⛔⛔ 交主 session 裁定：**D-15 未达成**
>
> D-15 要求「有代码改动的卡，Codex 多轮直到**绑最终 HEAD** 的一轮 BLOCKER/HIGH = 0」。
> 本卡跑了 r1/r2/r3 三轮，**每一轮都抓到 HIGH 且都已整改**；第 4 轮（绑最终 HEAD `f6ea5006`）
> **因 Codex 配额用尽无法完成** —— 完整 prompt 与最小探针**两次**都只回
> `ERROR: You've hit your usage limit`（证据 `codex-r4-quota-blocked-*.txt`，含复测自证）。
>
> ⇒ **没有任何一轮 Codex 绑到最终 HEAD。** 按协议 §2.1「0 字节存档重发一次，再 0 字节 →
> 主 session 人审替代，不等配额」。本卡**不自判通过**，请主 session 裁定：人审替代 / 等配额后补 r4。
>
> ⚠️ 需要留意的是：r1→r2→r3 每一轮都在**前一轮修复所开出的新面**上抓到 HIGH
> （见 §八 轮次表）。所以「r3 已修完」不等于「r4 会是 0 HIGH」——这是本卡最该被复核的地方。
> 证据目录: `_bmad-output/审查/evidence-lance-index-delete/`

---

## 一 本卡改了什么

`DELETE /api/v1/index/{vault_id}` 改前只看 `drop_vault_tables` 的 `int` 返回值，而

- 四道**整次拒绝**闸（清单降级 / 表名枚举失败 / 碰撞预检 / 模糊表名）全部 `return 0`，
- 「本 vault 名下一张表都没有」也是 `0`，
- 「每一张都 drop 失败」在 CARD-G2-9-F2 把返回值从「尝试数」改成「实删数」之后同样是 `0`，

三件性质完全不同的事于是共用同一个 `404 No tables found`；而**部分失败**回 `200` 且不带任何失败清单。

本卡把它拆成五态，并让 `drop_vault_tables` 出结构化回执：

| outcome | 语义 | HTTP | 响应体 |
|---|---|---|---|
| `no_tables` | 名下一张表都没有 | **404** | `detail` 文案**一字不改** |
| `refused` | 四道闸之一整次拒绝 | **409** | `{vault_id, refusal_kind, ambiguous_tables}` |
| `all_failed` | 每一张都 drop 失败 | **500** | `{vault_id, tables_failed:[{table, error_type}]}` |
| `partial` | 删成一部分 | **207** | `{vault_id, tables_dropped, tables_failed, partial:true}` |
| `dropped` | 全删成 | **200** | 体**一字不改** |

`refusal_kind` ∈ `{registry_degraded, listing_failed, collision, ambiguous}`（四道闸各一个）。

同卡收口的三项（均为 CARD-G2-9-F2 Codex 存档里的既有意见）：

- **(e1) r7 既有 HIGH**「V 缺项且余名恰为规范逻辑名」⇒ **建表即建指纹表**；
- **(e2) r5-M2 伪 vault** ⇒ 指纹来源加**形态核** + `LANCEDB_INDEX_TABLE_NAME` **配置后缀守卫**；
- **(e3) 自愈链默认分页** 4 个裸 `table_names()` 站点归零。

**r5-M1 只暴露不放宽**：历史逻辑名被整次拒删这件事，本卡只把它从「假 404」变成可见的
`409 + ambiguous_tables`，**没有**放宽任何一道闸。

---

## 二 契约与语义的零变化面（逐条自证点）

1. `drop_vault_tables(vault_id) -> int` 签名与返回语义（**实删数**）零变化 —— 两个消费方
   `endpoints/index.py` 与 `scripts/g29_dual_vault_canary.py:783` 的类型契约不动。
2. `_last_drop_failures`（`(表名, "ExcType: 原文")`）与 `_last_drop_refusal`（完整文案）
   两个诊断字段的**格式与内容**零变化 —— g29f1 既有门 `test_drop_vault_tables_accounts_for_swallowed_failures`
   断的就是它们。新回执 `DropVaultReport.failures` 是**另一份**、脱敏后的
   `(表名, "ExcType")`，两者分工不同。
3. 四道闸**一道都没放宽**：闸序、判据、`return`（现为 `refusal_kind` 填充）逐条对应。
4. 归属规则 `_owns_table` / `_table_owner` / `_known_vault_ids` 的**规则本体**零改动
   （(e2) 改的是来源③ 的**候选筛选**与配置项并入，不是最长前缀优先规则）。
5. `resolve_vault_group_id(vault_id)` 的 ContextVar 注入保留（Wave-5 既有契约）。
6. `api/v1/router.py` include 级 404/503 描述零改动。

---

## 三 DoD-3

### 4-A Claude 已代验（技术证据）

**第 0 分钟**（`prev-sha.txt`）：`pwd` = 车道树；分支 `card/p1-storage`；`status --porcelain` 0 行；
`PREV=5e0f87b7…`，语义核 `git log -1 --format='%s' | grep -c 'CARD-LANCE-DUALWRITE-NEVER-WRITES'` → **1**；
`git merge-base --is-ancestor 9c4e7e82 HEAD` → **rc=0**；红基线 `grep -vc '^#'` → **33**；
pyright `test -x` 自证通过。
**§〇 行号核对**：P1-A 只改 `edges.py` / `neo4j_client.py` 及其测试面，`lancedb_client.py` 与
`index.py` **零漂移** —— §〇 全部 file:line（`index.py` `delete_vault_index` span 91-120、
status_codes `[(105,503),(109,404)]`；`lancedb_client.py` `drop_vault_tables` 1325-1367、
`_drop_vault_tables_pinned` 1369-1457、refusal 赋值 1379/1392/1408/1436、`create_table` 1775/4429）
**逐字命中**，无需重锚。

**(b) 先红**（`ast-table-names-before-*.txt` / `c101-red-20260918T201551.txt`）：

| 判据 | 改前 | 改后 | 存档 |
|---|---|---|---|
| AST 裸 `self._db.table_names()`（无关键字） | `[1312, 4414, 4423, 4527]` = **4** | `[]` = **0** | `ast-table-names-{before,after}-*.txt` |
| 验伪锚：含关键字在内的同族总数 | `[898,1312,4414,4423,4527]` = **5** | `[964]` = **1**（`_all_table_names` 本体仍在） | 同上 |
| `delete_vault_index` 内 `HTTPException` status | `{503, 404}` | `{404, 409, 500, 503}` | 同上 |
| `grep -c 'status_code=207' index.py` | 0 | **1** | 同上 |
| `grep -cF 'def drop_vault_tables_report'` | 0 | **1** | 同上 |
| `grep -cF '_ensure_vault_fingerprint_table'` | 0 | **2**（def + 调用） | 同上 |
| 验伪锚：`grep -cF 'def drop_vault_tables('` | 1 | **1**（`int` 包装仍在） | 同上 |
| AST 自证：`drop_vault_tables` 体内调用 | — | `['drop_vault_tables_report']` | 同上 |

新门先跑（未改生产代码）**12 红 / 37 绿 / 收集 49**，红全部落在各自断言或运行期
（`AttributeError: … has no attribute 'drop_vault_tables_report'`），**无 collection error**：
`test_partial_failure_207…`（回了 dict 不是 JSONResponse）/ `test_all_failed_500`（404≠500）/
`test_registry_degraded_409_kind_not_404`（404≠409）/ `test_ambiguous_409_exposes_ambiguous_tables`（404≠409）/
`test_409_and_500_bodies_carry_no_exception_text_or_paths`（正向对照 `detail["refusal_kind"]` TypeError）/
`test_openapi_declares_409_207_500`（实有 `['200','422']`）/ g29f1 新增 6 条。
改后同一收集数 **49 passed / rc=0**（`c101-green-*.txt`）。

**(h) pyright**：`(cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')`
开工 `0 errors, 80 warnings` → 收工 `0 errors, 80 warnings`（`pyright-open-*.txt` / `pyright-close-*.txt`）。
⚠️ 中途一次读到 81 warnings：本卡在注释里**写出了** `pyright: ignore[...]` 的字面形态，
pyright 把注释当成真指令解析并判它 `reportUnnecessaryTypeIgnoreComment`。去掉字面形态后回到 80。
⚠️ 如实声明：pyright 检查面只含 `backend/app`（`pyrightconfig.json` 的 `include`），
**`lancedb_client.py` 不在其中** —— 它的类型自证靠 (g) 的真跑与 ruff。

**(i) 既有套件**：点名 6 文件 开工 **141 passed / rc=0**；终态点名 **8 文件**（6 + NEW c101 +
扩面 `test_edge_rationale_fallback.py`）**189 passed / rc=0**，0 本卡引入红。
⚠️ 文件顺序按**字母序**给 pytest —— 手工换序会人为暴露一处主干既有的 ContextVar 跨测试泄漏，
逐条对照见 **§七**。
`tests/regression` 目录级 **1913 passed, 6 skipped, 1 xfailed / rc=0**（`regression-close-*.txt`，
修复前后各跑一次，数字相同）。
W4 哨兵：全部跑次均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。

**开工 unit 基线**：`unit-open-*.txt` = 32 nodeids，与 `$BASE`（33）差集**只有一个 `<`**
（`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 在基线红、本树绿），
无 `>`。

**(m) 现网只读**（`live-readonly-*.txt`）：本卡改动的 5 个文件对
`-e 7691 -e 7687 -e canvas-learning-system/canvas-vault -e fsrs_bridge -e decay_beta`
命中数**全 0**；验伪锚（同一条命令喂 `neo4j_client.py` / `vault_scope.py`）分别 **3 / 1** ≥ 1。
全部测试数据在 `tmp_path`，`VAULTS_ROOT` 只在用例内 MonkeyPatch 并 `get_settings.cache_clear()` 进出各一次。

**lancedb 版本自证**（`lancedb-empty-fp-probe-*.txt`）：`lancedb 0.30.2 / pyarrow 23.0.1`；
`create_table(name, schema=pa.schema([...]))` 建出 4 列、`count_rows()==0` 的空表，
随后 `open_table + add` 正常接上（`_update_fingerprint` 的既有路径不受影响）。

**(g) 行为门与真库纪律**（终态，含 Codex r1 整改后新增的门）：

| 文件 | 用例数 | 其中卡文 (g) 所列 | 其余来源 |
|---|---|---|---|
| `test_index_delete_contract_c101.py`（NEW） | **10** | 8 | `listing_failed` 分辨门 + 其可达面门（r1 M-3） |
| `test_lancedb_cross_vault_drop_g29f1.py` 门⑨ 族 | **12** | 6 | 见下表 |
| `test_wave5_…` DELETE 段 | 4 | 3 | 新增 409 一条 |

门⑨ 族里**卡文没列的那 6 条**，逐条说明它们是为什么而加的 —— 每一条都对应一个
「本卡自己引入」或「Codex 抓到」的缺陷，不是凑数：

| 门 | 为什么加 |
|---|---|
| `…_add_documents_recreates_table_dropped_by_drift_guard` | **本卡自伤**：单快照漏掉漂移守卫的 `drop_table` ⇒ 写入静默全丢 |
| `…_fingerprint_table_is_retried_on_later_writes_after_a_failed_creation` | r1 HIGH-1：建失败后永不重试 |
| `…_fingerprint_source_keeps_a_real_table_with_an_older_schema` | r1 HIGH-2：列不齐的**真**指纹表被误排（漏报 = 丢数据） |
| `…_content_table_squatting_the_fingerprint_name_degrades_instead_of_losing_the_vault` | r2 HIGH-B：两个判据**互相抵消**（本卡引入的回归） |
| `…_rebuild_index_leaves_no_content_table_without_a_fingerprint_table` | r2 HIGH-A：重建拆掉归属保护 |
| `…_rebuild_index_keeps_the_fingerprint_table_when_the_rebuild_itself_blows_up` | r3 HIGH：上一条只覆盖**正常返回**路径 |

全部用 `tmp_path` 下真 LanceDB 库 + 真 `LanceDBClient`；`monkeypatch` 换掉的只有
`index._get_lancedb_client`（它返回的是**真客户端** = 依赖注入），以及 `_DropFailsOn` /
`_DropAlwaysFails` / `_ListTablesFails` / `_ListTablesFailsAfter` / `_CreateFailsOn` 五个
只在**一个方法**上注入失败的薄包装（故障注入 ≠ mock）。

**(k) 负控三段**（各只拆一层；EXIT trap 用 `git show HEAD:<path> > <path>` 还原；
⛔ 全部在**本卡 commit 之后**跑 —— commit 前跑 `git show HEAD:` 会把整轮未提交改动一起抹掉）：

| # | 拆掉的那一层 | 指定用例 | 结果 | 跑前/跑后 shasum |
|---|---|---|---|---|
| ① | `index.py` 的 `refused → 409` 改回落 404 | `c101::test_registry_degraded_409_kind_not_404` / `::test_ambiguous_409_exposes_ambiguous_tables` / `::test_listing_failed_409_and_is_only_reachable_for_bare_scope` | **3 failed, 6 passed**，正文 `AssertionError: … 必须是 409, 实为 404` | `381756f8…87e6` → `381756f8…87e6`（逐字同） |
| ② | `_vault_ids_from_fingerprint_tables` 的形态核短路（= 纯后缀推导） | `g29f1::test_configured_name_ending_with_fingerprints_does_not_forge_vault` | **1 failed, 40 passed**，正文 `普通向量表 'a_custom_file_fingerprints' 被按名字后缀反推成了伪 vault a_custom; V = ['a','a_b','a_custom']` | `7db5d02b…58c3` → `7db5d02b…58c3` |
| ③ | `add_documents` 建表分支后的 `_ensure_vault_fingerprint_table()` 调用 | `g29f1::test_index_only_vault_survives_shorter_id_drop_and_heal_when_undiscoverable`（+ `::test_first_content_table_creates_fingerprint_table_for_scoped_vault`） | **2 failed, 39 passed**，正文 `删 vault a 的索引连带删掉了 vault a_canvas 的表 a_canvas_nodes …; 消失的表 = ['a_canvas_nodes','a_vault_notes']` | `7db5d02b…58c3` → `7db5d02b…58c3` |

**Codex r1 整改后追加的两段**：

| # | 拆掉的那一层 | 指定用例 | 结果 | 跑前/跑后 shasum |
|---|---|---|---|---|
| ④ | 形态核回退成「四列齐全 **且** 无 vector」（r1 HIGH-2 的缺陷态） | `g29f1::test_fingerprint_source_keeps_a_real_table_with_an_older_schema` | **1 failed, 43 passed**，正文 `assert 'a_canvas' in set()` | `1dd900c8…d7bf` → `1dd900c8…d7bf`（逐字同） |
| ⑤ | (e1) 钩子挪回 `create` 分支内（r1 HIGH-1 的缺陷态） | `g29f1::test_fingerprint_table_is_retried_on_later_writes_after_a_failed_creation`（+ 分页门） | **2 failed**，正文 `第一次建指纹表失败后就再也没补过 …; 现存 = ['a_canvas_nodes']` | `1dd900c8…d7bf` → `1dd900c8…d7bf` |

**Codex r2 整改后再追加的两段**：

| # | 拆掉的那一层 | 指定用例 | 结果 | 跑前/跑后 shasum |
|---|---|---|---|---|
| ⑥ | 形态核排除占名表时**不置降级**（r2 HIGH-B 的缺陷态） | `g29f1::test_content_table_squatting_the_fingerprint_name_degrades_instead_of_losing_the_vault`（+ M2 锁） | **2 failed, 44 passed** | `c70df8ce…52af` → `c70df8ce…52af`（逐字同） |
| ⑦ | 去掉 `rebuild_index` 返回前的补建调用（r2 HIGH-A 的缺陷态） | `g29f1::test_rebuild_index_leaves_no_content_table_without_a_fingerprint_table` | **1 failed, 45 passed**，正文 `重建删掉指纹表后没有补回来 …; 现存 = ['a_canvas_nodes']` | `c70df8ce…52af` → `c70df8ce…52af` |

**Codex r3 整改后再追加的一段**：

| # | 拆掉的那一层 | 指定用例 | 结果 | 跑前/跑后 shasum |
|---|---|---|---|---|
| ⑧ | 退回 r2 态（去掉「删完立刻补」+ 拆掉 `try/finally`） | `g29f1::test_rebuild_index_keeps_the_fingerprint_table_when_the_rebuild_itself_blows_up` | **1 failed, 46 passed**，正文 `重建中途抛异常后指纹表没了 …; 现存 = ['a_canvas_nodes']` | `0ad5e339…d2c3` → `0ad5e339…d2c3`（逐字同） |

存档：`negctl-{1..8}-*.txt`（各含跑前/跑后 shasum 两行 + `pytest_rc=1`）。八段跑完
`git status --porcelain` 无已跟踪改动。
⑥⑦⑧ 三段的脚本里加了**前置守卫**（`git diff --quiet HEAD -- $F` 不成立就 `REFUSED` 退出）。
⚠️ 另有一次**未提交状态下**的缺陷态自证（新门写完、还没 commit 时），那次刻意**不用**
`git show HEAD:` 还原，改用文件副本 + `shasum` 逐字对照 —— 同一个坑不踩第三次。
⑥⑦ 两段的脚本里加了**前置守卫**（`git diff --quiet HEAD -- $F` 不成立就 `REFUSED` 退出）——
就是下面那条教训的处置。

### ⚠️ 我又踩了一次自己记过的坑（如实记录）

负控④ **第一次**是在 commit **之前**跑的，于是 EXIT trap 的 `git show HEAD:<path> > <path>`
把当时**未提交**的两处 HIGH 修复一起抹掉了 —— shasum 跑前 `1dd900c8` ≠ 跑后 `f1c67314`，
这个不一致就是它暴露出来的。
处置：按 shasum 差异立刻发现 → 核实损失范围（只有 `lancedb_client.py`，测试文件幸存）→
重新应用两处修复 → **先 commit 再重跑负控**（第二次 shasum 逐字同）。
本卡前三段负控是在 commit 之后跑的、没问题；这一次是我自己打破了那个顺序。
**顺序铁律**：改完 → commit → 跑负控。
③ 的红**落在锁本身**（不是夹具形态断言）—— 这是本卡特意调整过断言顺序换来的：把机制断言
（V 里有没有 `a_canvas`）放到 drop 之后，负控才读得出"锁住的那张表到底有没有被删"。

**(六) ruff**（`ruff-close-*.txt` / `ruff-format-scope-*.txt`）：

- `ruff check`：zsh 数组口径 `git diff --name-only --diff-filter=AM 9c4e7e82 HEAD -- '*.py' ':(exclude)_bmad-output'`
  → `files=12`（车道累计面，含 P1-A 的 6 个文件），`All checks passed! rc=0`。
- 验伪锚（`ruff-anchor-*.txt`）：仓内临时文件 F821 → **rc=1**；
  `backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]` 里**没有 F401**，恒不触发，故不作锚。
  跑后 `git status` 无 `_anchor_tmp` 残留。
- `ruff format --check`：**本卡面 6 个文件 `6 files already formatted, rc=0`**。
  车道累计面上有 4 个文件 dirty（`neo4j_client.py` / `test_mock_degradation_transparency.py` /
  `test_neo4j_client.py` / `test_review_mode_support.py`）—— 三条证据证明**与本卡无关**：
  ① 它们的 `PREV..HEAD` diff 行数**全为 0**（本卡零改动）；
  ② 把它们的 **PREV 态**取出来单独跑 `ruff format --check`，**同样 dirty**（`rc=1`）；
  ③ 它们全是 P1-A 面。已登记，留给 P1-A 或主 session。


**(l) 地盘门**（`territory-*.txt`，post-commit）：
`git -c core.quotepath=false --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'`
= 恰 5 个文件，全部在卡文 (l) 白名单内：

```
backend/app/api/v1/endpoints/index.py
backend/lib/agentic_rag/clients/lancedb_client.py
backend/tests/unit/test_index_delete_contract_c101.py        (NEW)
backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py
backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py  (声明扩面)
```

⛔ 不含 `openapi.json` / `edges.py` / `neo4j_client.py` / `memory_service.py` / `router.py` /
`vault_scope.py` / 任何 conftest / 任何别车道文件。`g29_dual_vault_canary.py` **零改动**
（(e1) 只在**新建**内容表时多建一张指纹表，canary 的 LanceDB 段期望值未受影响 —— 见 §四 ⑤）。
`test_wave5` 的 `-U0` hunk 头全部 ≥ `@@ -466`，即改动行全在 :463 之后的 Test 10 段内。
✅ **验伪锚已补跑**（`territory-final-*.txt`，docs commit 之后）：
带 `':(exclude)_bmad-output'` 时 `_bmad-output/` 命中 **0**，去掉后命中 **67** ——
锚不再空洞，地盘门确实在排除，不是恒空。
（此前那次跑锚是空洞的：证据尚未入库，`git diff` 看不见未跟踪文件。）

**(j) openapi**：3 个 commit —— `db9bf6d1`（代码与门，被 `spec-sync-flat` 顺带塞入
`backend/openapi.json`）→ `bbb72916`（**只含** `openapi.json` 的还原 commit，staged 只有 json
⇒ 两条 spec-sync glob 均不命中，零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`）→ `d6b7fa42`（补门）。
`git --no-pager diff --no-color $PREV HEAD -- backend/openapi.json | wc -l` → **0**（净零）。
`tests/contract/test_openapi_snapshot_drift.py` 收工**预期红**（`openapi-drift-*.txt`），
且差异**只有**本卡这一条路径：

```
>paths>/api/v1/index/{vault_id}>delete>description   (docstring 变长)
>paths>/api/v1/index/{vault_id}>delete>responses>207  仅在 app.openapi()(snapshot 缺失)
>paths>/api/v1/index/{vault_id}>delete>responses>409  仅在 app.openapi()(snapshot 缺失)
>paths>/api/v1/index/{vault_id}>delete>responses>500  仅在 app.openapi()(snapshot 缺失)
```

登记：**待主 session 集成期再生**。

**(i) `tests/unit` 目录级收工**（`unit-close-20260919T0100*.txt`，HEAD `f6ea5006`，**独占**执行，
跑法与开工基线逐字同、不带 `--ignore`）：

```
= 33 failed, 5770 passed, 44 skipped, 13 xfailed in 374.36s (0:06:14) =
diff(base, close)  → rc=0，与红基线 33 条**完全相同**（连一个 `<` 都没有）
close nodeids = 33
```

⇒ **零本卡引入红**。passed 从开工 5748 → **5770**（+22 = 本卡新增门数：c101 10 + g29f1 12 −
原有计数差 + wave5 1）。

⚠️ `diff(open, close)` 有一个 `>`：`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。
它**不是**本卡引入 —— 三条证据：① 它**在红基线里**（`grep -c` = 2 行命中）；
② 开工跑时它偶然绿了一次（所以开工是 32、基线是 33），是 **flaky**；
③ 本卡改动面 6 个文件里没有 `candidate_service`（`git diff --name-only` 实测）。
卡文 (i) 的判据是「与 `$BASE` diff 只允许 `<`」—— 现在无差异，通过。


### ⚠️ 本卡自己引入又自己抓到的一个真缺陷（如实记录）

**缺陷**：(e3) 收口默认分页时，我把 `add_documents` 里**两次** `table_names()` 枚举合并成了
一次 `_all_table_names()` 快照。但两次枚举**之间**夹着 `_check_and_fix_dimension_mismatch` ——
它检测到 schema 漂移时会**把表 drop 掉**（其 docstring 原话：*"True if the table was dropped
(caller should create new)"*）。沿用漂移检查**之前**的快照 ⇒ 下面去 `open_table` 一张刚被删掉的
表 ⇒ 异常被 `add_documents` 外层的 `except` 吞成 **`return 0`**，调用方看到"添加了 0 条"，
**写入静默全丢**。

改前的实现是靠"第二次重新查一遍 `table_names()`"歪打正着地躲开这一点。

**为什么点名套件没抓到**：本卡的点名 6 套件 + `tests/regression` 在缺陷态下**全绿** ——
"漂移表 + 同名 `add_documents`"这条组合路径原先没有任何门。

**修复**：接住守卫的返回值（`if self._check_and_fix_dimension_mismatch(...): table_exists = False`），
不再依赖任何一次枚举去推断"表还在不在"。

**锁**：新增 `g29f1::test_add_documents_recreates_table_dropped_by_drift_guard`，
断言落在**行数**上（只断"表还在"不够 —— 两条分支最后都可能留下同名表，区别在数据有没有进去）。
负控式自证：把实现回退成单快照，该门立刻红成
`AssertionError: … 写入静默全丢。实得 0 / assert 0 == 3`，还原后 51 passed。

**教训**（已进台账）：把「两次查询」合并成「一次快照」时，必须逐个检查**两次查询之间**有没有
改变被查状态的调用。这类重构看起来是纯性能/口径收口，实则把一个隐式的"重新读一遍"契约删掉了。

### ⚠️ 一条我先说错、后被自己推翻的解释（如实记录）

`tests/unit` 收工跑在 `test_deploy_vault_sh.py` 段出现 `F`，而同一文件在**开工基线**全绿。
我最初把它归因为「我并发跑了别的进程造成 CPU 争用」，并据此把收工跑改成**独占**。

**独占之后同一段仍然红** —— 那个解释站不住。真正的机理要读**失败正文**才看得出来
（脚本自己的 5s 墙钟上限先开火），逐条定性见 **§六**。

教训：「同一文件开工绿收工红」这个形态，我一度只凭「它有 subprocess+timeout」就下了结论，
没有去读失败正文。**形态相似不是归因**。

⚠️ 另作废并删除了两次中断跑的部分存档（没跑完的探针不产出阴性结论）。

### 4-B 用户能感知的变化（零技术词）

我删掉一门课的搜索索引时，系统会老实告诉我到底是删干净了、一张都没删成、还是它为了保护别的课主动
没删——以前这三种情况都长得一样，都只回一句「没找到东西可删」。更要紧的是「删了一半」：以前它回
「成功」，我就真以为清干净了，其实还剩几块躺在那儿；现在它会把**剩下的是哪几块**列给我看。

**felt-sense**：以前按完那个删除键，我心里是空的——它说「没找到」，我不知道是真没有，还是它拦住了
我、或者它自己失手了。我只能去别的地方翻，或者干脆再点一次。现在那句回话里有东西可抓：要么告诉我
删了几张，要么把它没敢动的那几张名字摆出来。第一次看到「它为了保护另一门课主动没删」这句话的时候，
我的反应是「哦，原来它是在替我挡」，而不是「这破按钮又坏了」。

---

## 四 本卡未证明什么

1. **未证明改前建的表已安全**：(e1) 只覆盖**此后**新建的内容表。改前就已存在、目录不可发现
   且没有指纹表的 vault，它的表**仍然**会被 id 更短的 vault 认领——本卡**不追溯**存量
   （卡文 §三：D-41 现网备份对账是用户授权项，本卡不碰现网）。
2. **未证明现网 lancedb 行为与 tmp 实测一致**：空指纹表建法在本树实测的是
   `lancedb 0.30.2 / pyarrow 23.0.1`（证据 `lancedb-empty-fp-probe-*.txt`）。现网只读，未跑。
3. **未证明 `get_all_vault_stats` 的归组正确**：本卡只把它的**枚举口径**从默认分页换成全量，
   `tname.split("_", 1)[0]` 的归组口径**没动**——互为前缀的 vault 在 stats 里仍会被归错组。
4. **未证明 r5-M1 场景的可用性**：历史逻辑名被整次拒删这件事，本卡只让它**可见**（409 +
   `ambiguous_tables`），**没有**给出「怎样才能删掉」的路径。放宽需要「经确认的归属清单
   或表级元数据」（Codex r7 原话），移交。
5. **未证明 canary 全链**：`g29_dual_vault_canary.py` 需要 Neo4j 的段本卡不跑（零 7691/7687）。
6. **未证明 openapi 再生后漂移门转绿**：`tests/contract/test_openapi_snapshot_drift.py` 收工
   预期红（新响应码未再生），由主 session 集成期再生后复核。
7. **未证明「配置名撞指纹后缀」场景下 vault 还能删索引**：见 §五 ③ —— 终态是**可见的 409
   ambiguous**，不是「能删了」。
8. **未证明 (e1) 在 `index_canvas` / `index_vault_notes` 的完整链路上端到端生效**：钩子挂在
   `add_documents` 的建表分支（那是这三条索引路径最终建表的地方），但本卡只在 `add_documents`
   这一层做了真库验证，没有跑一次完整的 `index_canvas`（它需要 embedding 模型）。
9. **未证明 canary 的期望值不受 (e1) 影响**：`g29_dual_vault_canary.py` 本卡零改动，推理是
   (e1) 只在**新建**内容表时多建一张指纹表；但 canary 需要 Neo4j，本卡没跑，**未实测**。
10. ~~**未证明 `listing_failed` 在 scoped vault 上真的不可达**~~ —— **该主张已被推翻并撤回**。
    Codex r1 MEDIUM-3 指出这条推理不成立；本卡随后给出了那个输入（枚举**瞬时**失败）并加了门
    `c101::test_listing_failed_reachable_on_scoped_vault_with_a_transient_failure`，
    实测**确实可达**。原「only bare scope」的门已改名收窄。这条从「未证明」升级成「已证伪」。
11. **未证明 `attempted` 非空而 `dropped`/`failures` 同时为空不可能**：`outcome` 的完备性依赖
    「每张 attempted 的表要么进 dropped 要么进 failures」，这是读代码得到的，不是门锁住的。
12. **未证明「每次写入都补建指纹表」的代价可接受**（Codex r2/r3 两次更正后的完整口径）：
    健康且 TTL 命中时，每次 **scoped** vault 的成功写入多一次**全量表名枚举** +
    一次 `open_table` 读 schema（r2 HIGH-B 之后早退判据要与形态核同口径，不止枚举那一下）。
    **降级结果不缓存**，所以两次指纹表名求值可能各自重扫目录与全部候选。
    启动路径原本就打开全部表，现在还会额外检查全部后缀候选。
    ⛔ 我先前写的「候选数 = vault 数」是**过强主张**，已撤回 —— 候选数是**所有后缀匹配表数**。
    本卡**没有任何性能实测**：既不能说代价可忽略，也没有证据说它已成为瓶颈。
13. **未证明形态核放宽后 r5-M2 面没有被重新打开**：r1 HIGH-2 把排除条件收窄为「只有带 `vector` 列」。
    门里有排他断言（带 vector 的那张仍被排除），但**没有**枚举「无 vector 列、名字以
    `_file_fingerprints` 结尾、却不是指纹表」在生产上还有没有别的产出路径。
14. **未证明 (e1) 覆盖了所有建内容表的站点**：钩子只挂在 `add_documents`。
    `create_table` 在 `lancedb_client.py` 里另有一处（`_update_fingerprint` 建指纹表本身），
    但 `index_image_content` / `rebuild_index` 等是否全部经 `add_documents` 落表，**本卡没有逐一追**。
15. **未证明那处 ContextVar 泄漏（§七）在生产上有后果** —— 目前只观测到测试间的顺序依赖。
16. **未证明 HIGH-B 的 fail-closed 代价面已被穷尽**：我在注释里写「任何带 `vector` 且名字以
    `_file_fingerprints` 结尾的表会把整库打成降级」。Codex r3 更正了其中一句：停的是所有
    **scoped** vault，**default／空口径仍跳过降级闸**。并且「只改回配置**不会**移除已有的
    占名表，降级会持续」—— 运维必须**改表名或删表**才能退出降级。本卡没有提供退出工具。
17. **未证明「删完立刻补」把窗口收窄到了可接受程度**：`_ensure_vault_fingerprint_table`
    自己要读 schema 再 `create_table`，那之间仍有失败面；`index_vault_notes` 的
    `force_rebuild=True` 路径是否会**再次**删掉这张空表，本卡**没有逐行追**（若会，
    `finally` 那次补建就是唯一屏障，窗口并没有收窄）。这条已写进 r4 的 prompt 请 Codex 核。
18. **未证明 `partial` 终态不会留下「有内容、无指纹」**：Codex r3 指出指纹表删成功、内容表
    删失败时就会。那是**基线既有**的部分失败行为，本卡未改、未加门。

---

## 五 台账待登记条目

1. **`DELETE /index/{vault_id}` 契约变化**（可观察）：无表 404 / 拒绝 409 / 全失败 500 /
   部分 207 / 全成 200；体字段与脱敏口径（只含表名 / `refusal_kind` / `error_type`，
   异常原文与路径只进服务端日志）。修复 sha `<收工填>`，门 nodeid 见 §三。
2. **openapi 待主 session 集成期再生**：本卡 commit **不含** `backend/openapi.json`
   （首个代码 commit 被 `spec-sync-flat` 顺带塞入后，紧接一个只含该文件的还原 commit
   `<收工填>`）；`test_openapi_snapshot_drift.py` 收工预期红。
3. **卡文 (g) 与 §三 对 M2 锁的措辞不一致，本卡按 (g) 实现并加强**：(g) 写「drop 不被**闸③**拒」，
   §三 写「drop 不被拒」。实测终态是**闸④ ambiguous 整次拒绝**（卡文 (e2) 括注明写并接受
   「该表随后会被闸④当模糊名整次拒绝——可见、不静默」）。本卡的 M2 锁同时断
   ① `a_custom ∉ V` ② `refusal_kind != "collision"`（r5-M2 症状消失）
   ③ 终态 `refusal_kind == "ambiguous"` 且 `ambiguous == ("a_custom_file_fingerprints",)`。
   请主 session 复核这条口径。
4. **新文件与扩面文件**：新增 `backend/tests/unit/test_index_delete_contract_c101.py`；
   扩面 `backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py`（只改 Test 10
   的三条 DELETE 用例 + 新增 ≤2 条）。两者草案地盘表均未列，请主 session 集成期核零交集。
5. **既有意见处置**：r7 HIGH = (e1) 建表即建指纹表（新表闭合、存量登记 D-41）；
   r5-M2 = 形态核 + 配置后缀守卫；r5-M1 = 只暴露不放宽（移交）；
   r5-LOW `_pinned_vault_ids` 嵌套**未动**（钉住登记）。
6. **分页 4 站点归零**：`get_all_vault_stats` / `add_documents` ×2 / `count_documents_by_canvas`
   全部改走 `_all_table_names()`；`get_all_vault_stats` 的 `split("_", 1)` **归组口径未改**。
7. **canary 过时 docstring**：`g29_dual_vault_canary.py:771-773` 仍写「返回值是尝试删的表数」，
   与 CARD-G2-9-F2 之后的实删数语义不符 —— 本卡**未改**（避免越界），登记。
8. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数**：`<收工填>`。
9. **卡文 §〇 行号核对结果**：P1-A 只碰 `edges.py` / `neo4j_client.py` 及其测试面，
   `lancedb_client.py` 与 `index.py` **零漂移**，§〇 全部 file:line 逐字命中。
10. **本卡 commit 序列**（主 session squash 时按此顺序取，共 5 个代码/测试 commit + 1 个 docs）：
    | # | sha | 内容 |
    |---|---|---|
    | 1 | `db9bf6d1` | 代码与门（(c)(d)(e1)(e2)(e3) + c101 8 条 + g29f1 6 条 + wave5 改写） |
    | 2 | `bbb72916` | 把 `backend/openapi.json` 还原到 PREV 态（净零） |
    | 3 | `d6b7fa42` | 补 `listing_failed` 闸②门与其可达面对照 |
    | 4 | `2e331c49` | 修 `add_documents` 单快照缺陷 + 回归锁 |
    | 5 | `3c45f9ad` | P1-A 分页外追加门按其自身指令翻正（**地盘扩面**） |

    卡文 (g) 未列第 3/4/5 条；补它们的理由分别是「`refusal_kind` 四个取值里 `listing_failed`
    原本没有任何门」「本卡自己引入的写入丢失缺陷需要一条锁」「不翻正它就是本卡引入的红（阻断）」。
11. **P1-A 占位门已到期，本卡按其指令翻正（地盘扩面 ②）**：
    `backend/tests/unit/test_edge_rationale_fallback.py::test_lancedb_real_write_second_append_beyond_pagination_fails_loudly`
    → `::test_lancedb_real_write_appends_beyond_default_pagination`。
    该文件属 **P1-A 面**，不在卡文 (l) 白名单，请主 session 集成期核零跨车道交集。
    详见 §六 ①。P1-A 验收单里「上游分页限制」那条登记**可以销账**了。
12. **`test_deploy_vault_sh.py::test_preflight_npm_build_*` 5 条的硬编码墙钟上限**（建议另立卡）：
    `cap = 5` 秒写死在测试里，而被测脚本会在到点时杀掉整个进程组。机器稍慢就红，
    且红的样子与真缺陷一模一样。详见 §六 ②-⑥。
13. **`refusal_kind` 的可达面登记**：`registry_degraded` / `collision` / `ambiguous` 在
    scoped vault 可达；`listing_failed` 只在**裸表口径**可达（scoped 侧同一注入会先被闸①拦）。
    这条推理已写进门的 docstring 与对照断言，请主 session 复核。
14. **一次 CPU 争用造成的假红**（方法论，建议进工程坑索引）：
    `tests/unit/test_deploy_vault_sh.py` 244 个用例**每个**都 `subprocess` + 墙钟 timeout，
    对同机并发极敏感 —— 与另一轮 pytest / pyright / lefthook `spec-sync-flat` 同时跑会
    集体超时变红，**看起来完全像"本卡引入红"**。目录级收工跑必须独占执行。
15. **pyright 会把注释里"提到"的抑制指令当真指令解析**：本卡在解释性注释里写出了
    `pyright: ignore[...]` 的字面形态，warnings 立刻从 80 涨到 81
    (`reportUnnecessaryTypeIgnoreComment`)。改掉字面形态即回落。建议进工程坑索引。

16. **主干既有的 ContextVar 跨测试泄漏（本卡发现，未修）**：`test_wave5_…` 的
    `TestVaultIdResolverShared` / `TestContextVarInjectionFromResolver` 两个**本卡零改动**的
    既有类直接调 `resolve_vault_group_id`，它 `set_current_subject_id(...)` 写的 ContextVar
    **不随 `with patch(...)` 恢复**，泄漏给后跑的测试并改写它们的 `active_vault_id`。
    字母序目录级跑里不显现（`test_edge_…` 排在 `test_wave5_…` 之前）。
    根治需要给 ContextVar 加 autouse reset fixture，而 `conftest` 是 P9 唯一写者、本卡禁改。
    逐条对照见 §七。建议另立卡。
17. **Codex r1 的 2 HIGH 均已改代码并各配负控**（`3a4c1c35`）：
    HIGH-1 指纹表建失败后永不重试（钩子挪出 create 分支）；
    HIGH-2 列不齐的**真**指纹表被误排（排除条件收窄为「只有带 `vector` 列」）。
    两条都是**本卡初版自己引入**的，不是遗留面。
18. **Codex r1 的 4 MEDIUM 均已处置**（`4ce4b819`）：M-3 收窄「only bare scope」这条**过强主张**
    并补上它指出的那个输入；M-4 如实标注空洞格 + 更正「`file_fingerprints` 有 409 终态」这条
    **过强表述**；M-5 把 207 纳入脱敏门；M-6 五态门改双库、五格全部真调 int 包装。
19. **Codex r1 的 3 LOW 登记不阻断**：负控异常类型硬编码 `RuntimeError`（应混用
    `PermissionError` 等）；c101 未直接覆盖 `collision → 409`（g29 只覆盖 report 层）；
    r7 自愈门未独立覆盖**冷启动**路径（它在同一客户端 drop + 显式刷新 V 之后才跑）。
20. **本卡引入又自行修掉的缺陷（必须登记，不是"过程"）**：`add_documents` 把两次表名枚举合并成
    单快照后，漂移守卫 drop 掉表的场景会走进坏掉的 add 分支 ⇒ 返回 0 ⇒ **写入静默全丢**。
    修复 = 接住 `_check_and_fix_dimension_mismatch` 的返回值；锁 =
    `g29f1::test_add_documents_recreates_table_dropped_by_drift_guard`（负控式自证已跑）。
    ⚠️ 这条路径**在本卡之前也没有任何门** —— 点名套件与 `tests/regression` 在缺陷态下全绿。
    建议主 session 复核：同族「两次读取之间夹着会改状态的调用」在 `lancedb_client.py` 里
    还有没有别处（本卡只查了 `add_documents`）。

---
21. **⛔ D-15 未达成，交主 session 裁定**：Codex r4（绑最终 HEAD `f6ea5006`）因**配额用尽**
    无法完成 —— 完整 prompt 与最小探针**两次**均 0 字节（证据 `codex-r4-quota-blocked-*.txt`，
    含复测自证：**没有**继承第一次的报错）。按协议 §2.1「再 0 字节 → 人审替代，不等配额」。
    **人审输入已备好**：`_bmad-output/审查/CARD-LANCE-INDEX-DELETE-CONTRACT-人审清单-r4替代.md`
    （r3 审 SHA → 最终 HEAD 只有 **2 文件 / 116+ / 37−**，其中**唯一的行为改动**是
    `rebuild_index` 的指纹表窗口，其余 6 处是 r3 LOW-1 点名的说明同步）。
22. **⛔ 产品面取舍请裁**：r2 HIGH-B 的修法是 **fail-closed** —— 指纹表名被一张带 `vector` 的表
    占住时，形态核排除它的同时**置降级**，于是**所有 scoped vault** 的删索引与维度自愈都停
    （default／空口径不受影响）。**只改回配置不会移除已有占名表**，降级会持续，运维必须改表名
    或删表，**本卡未提供退出工具**。我的判断是「可见地停」优于「静默删掉别人的表」，请复核。
23. **这道保护仍有两条已知不生效的路径**（均已登记、本卡未改，建议另立卡）：
    ① `partial` 终态（指纹表删成功、内容表删失败）又会变成「有内容、无指纹」——**基线既有**；
    ② `initialize()` 先跑 `_cache_tables()`，早于任何写入钩子 ⇒ 不能声称「任何破坏性路径之前
    指纹表必已建成」。
24. **Codex r2 / r3 的处置汇总**：r2 的 2 HIGH（`1610f01b`）+ r3 的 1 HIGH（`f6ea5006`）
    各配负控⑥⑦⑧，全部红在指定断言且 shasum 逐字同；r2 LOW-1 与 r3 LOW-1 的说明同步共 10 处，
    其中一条是**事实陈述写错了**（`DropVaultReport` docstring 称「两个消费方零改动」，
    实际 `index.py` 已改调 report）。r2 LOW-2 / r3 LOW-2、LOW-3 登记不阻断。


## 六 收工 `tests/unit` 的新增红 — 逐条定性

`unit-close-20260918T214741.txt`（HEAD `2e331c49`）相对开工跑有 **6 条 `>`**。逐条：

### ① `test_edge_rationale_fallback.py::test_lancedb_real_write_second_append_beyond_pagination_fails_loudly`

**归属：本卡引入 —— 已处置（不是遗留）。**

这是 P1-A（本车道上一张卡）留下的**占位门**：当时卡文硬边界不许改
`lancedb_client.add_documents`，所以只能把「上游分页限制下第二次追加会**响亮失败**」钉住并登记。
它的失败消息原文就是操作指令：

> 「若哪天它真的成功了，说明上游已修，**请删掉本门并把 G1② 的 append-only 覆盖到分页外场景**」

本卡 (e3) 正是它说的「另立卡改上游走 `_all_table_names()`」。按指令翻正：
改名 `test_lancedb_real_write_appends_beyond_default_pagination`，判据从「坏了会说」换成
**G1② append-only 在分页外的正向覆盖**（同一条 edge ⇒ 2 行 + `doc_id` 集合 + `edge_id` 同一）。
两条前提断言保留并加强（`len(db.table_names()) == 10` + 「目标表不在默认分页内」）——
缺任一条本门就退化成 `test_lancedb_real_write_is_append_only` 的重复，一点分页面都没覆盖到。
修复 commit `3c45f9ad`；该文件单跑 **28 passed / rc=0**。

⚠️ **地盘扩面声明**：`backend/tests/unit/test_edge_rationale_fallback.py` 属 P1-A 面，
不在卡文 (l) 白名单。不改它这条门就是本卡引入的红（按 (i) = 阻断）。同车道串行、零跨车道交集。

### ②-⑥ `test_deploy_vault_sh.py::test_preflight_npm_build_*`（5 条）

**归属：主干既有的时序敏感（在高负载目录级跑下不稳），不是本卡引入。** 三条独立证据：

1. **失败机理直接可读**：5 条**全部**倒在同一句 —— 脚本自己的墙钟上限先开火：
   `[1/6] preflight: FAIL npm run build 超时（墙钟上限 5s, 已杀 npm 所在进程组）`，
   随后测试的前提断言 `_npm_was_invoked(pids)` 为假（假 npm 连 PID 都没来得及落盘）。
   其中 `test_preflight_npm_build_cap_does_not_kill_a_fast_build` 是「**不该被杀的快 build**」
   —— 它也被 5s 上限杀了，这只能是墙钟，不可能是逻辑。
2. **独占单跑全绿**：5 条一起单跑 **5 passed / 33.91s**（`deploy-npm-standalone-*.txt`）。
3. **本卡零触碰它们读的任何东西**：本卡面 5 个文件全在 `backend/`；
   `git diff --name-only 9c4e7e82 HEAD -- scripts/ frontend/ package.json '*.sh'` = **空**；
   `scripts/deploy-vault.sh` 最近一次改动是第十四批的 `8eeaa899`（2026-09-17），与本卡无关。

⚠️ 如实声明**未做**的那一步：没有在主干 `9c4e7e82` 上复跑整个 `tests/unit` 来直接复现这 5 条 ——
车道树不切主干。上面三条是结构+机理证据，不是「在主干上也红」的直接观测。
建议主 session 集成期在候选树上留意它们；若要根治，应给这 5 条一个与机器负载无关的
`cap`（现在硬编码 5s）或标记为 load-sensitive。

分类口径（协议 §4）：主干既有 / 门抓到的既有偷连 / 本卡引入（阻断）。

---

## 七 一处**主干既有**的 ContextVar 跨测试泄漏（本卡发现，未修，登记）

**怎么被发现的**：我在点名套件里把 `test_edge_rationale_fallback.py` **手工放在最后**，
于是 `test_lancedb_real_write_via_endpoint[neo4j-ok-200]` / `[neo4j-down-207]` 两条红了
（`assert expected_table in db.table_names()`）。单跑那两条是绿的 ⇒ 跨文件污染。

**逐条对照（全部实测）**：

| 对照输入 | 结果 |
|---|---|
| `wave5 + edge`（我原来的顺序） | **2 failed** |
| 把 `wave5` 换成 **PREV 态**（本卡改动前的版本）再跑同一对 | **4 failed**（edge 那 2 条照样红） |
| 只用 PREV 就有的 `::test_delete_vault_index_injects_contextvar` + edge | 29 passed |
| 只用本卡**新增**的 `::test_delete_vault_index_409_when_refused` + edge | 29 passed |
| 逐类二分 | ❌ `TestVaultIdResolverShared`、❌ `TestContextVarInjectionFromResolver`（**本卡零改动**的既有类） |
| 顺序反过来 `edge + wave5`（= 字母序目录级的真实顺序） | 65 passed |

**定性：主干既有，本卡零贡献。** 机理：那两个类直接调 `resolve_vault_group_id(...)`，它会
`set_current_subject_id(group_id)` 写 **ContextVar**；ContextVar 不随 `with patch(...)` 恢复，
于是泄漏给后跑的测试 —— 后者的 `active_vault_id` 被改写，`resolve_table_name` 拼出的前缀就变了。

**为什么之前没人撞上**：`tests/unit` 目录级按**字母序**跑，`test_edge_rationale_fallback.py`
排在 `test_wave5_…` **之前**。是我手工换序才把它暴露出来。

**本卡处置**：点名套件的文件顺序改成**字母序**（与目录级一致），**不修**这处泄漏 ——
它在 `wave5` 的既有类里，属别的面，且修它需要给 ContextVar 加 autouse 的 reset fixture，
而 `conftest` 是 P9 的唯一写者、本卡硬边界禁改。**已登记，见 §五 ⑰。**

⚠️ 如实声明：我**没有**去证明「这处泄漏在生产上有后果」——它目前只是测试间的顺序依赖。

---

---

## 八 Codex 轮次与逐条处置

| 轮 | 绑定 SHA | B / H / M / L | 结论 |
|---|---|---|---|
| r1 | `3c45f9ad` | 0 / **2** / 4 / 3 | 实现缺陷 + 过强主张 |
| r2 | `4ce4b819` | 0 / **2** / 0 / 2 | 确认 r1 六条已修；抓出**修复引入的新耦合** |
| r3 | `1610f01b` | 0 / **1** / 0 / 3 | 确认 HIGH-B 成立；HIGH-A **修得不彻底** |
| r4 | `f6ea5006` | **未完成（配额）** | 完整 prompt 与最小探针两次均 0 字节；证据 `codex-r4-quota-blocked-*.txt` |

存档：`_bmad-output/审查/codex-review-CARD-LANCE-INDEX-DELETE-CONTRACT-r{1,2,3,4}.md`。
每轮都用 `gpt-6-astra` + `model_reasoning_effort=ultra`，`codex-cli 0.153.3`。

⚠️ **轮次的收益不是递减的重复，而是逐层往里**：r1 抓实现缺陷与过强主张 → r2 抓**修复本身
引入的新耦合**（形态核 × 存在性早退互相抵消）→ r3 抓**修复只覆盖了正常路径**（异常/取消与
重建期间的窗口）。单轮审查会停在 r1 那个状态，而那时 r2 的 HIGH-B 已经存在了。
这正是 D-15「多轮直到绑最终 HEAD 且 HIGH=0」要挡住的东西。

**r2 确认 r1 的 6 条全部实质修复**（原文：「r1 的追加重试、旧 schema 保留、瞬时枚举门、
207 脱敏和五态 int 包装均有实质修复」），并抓出 **2 条新 HIGH** —— 都在 (e1) 的**完整性**上，
不是重提：

### r2 HIGH-A：`rebuild_index` 会拆掉归属保护，且不触发补建钩子

`rebuild_index` 先 `drop_table(fp_table)` 再 `drop_table(table_name)`，然后调 `index_vault_notes`。
若该 vault 下**没有 Markdown**，`index_vault_notes` 不写任何文件 ⇒ 不走 `_update_fingerprint`
⇒ 指纹表不再存在；而 canvas 内容表 `a_canvas_nodes`（不是 `vault_notes`）**没被删**，仍在库里。
⇒ 该 vault 有内容表、无指纹表 ⇒ **r7 场景重现**：短 vault `a` 的 drop 与自愈都能认领它。

⚠️ 不需要并发或故障注入，也不是 D-41 排除的旧存量。门⑨ 在写入后**直接**测删除/自愈，
没有插入「重建生命周期」这一段。

**站点枚举（避免只修一处）**：`lancedb_client.py` 里 4 个 `drop_table` 站点中，
删**指纹表**的只有 `rebuild_index:2129`；其余三处删的都是内容表
（`:2136` 内容表 / `:4594` 漂移守卫 / `:1644` `drop_vault_tables` 有意整删）。
`app/` 侧 `metadata.py:576` 删的是 `resolve_table_name("vault_notes")` = 内容表，不是指纹表。

### r2 HIGH-B：「存在即早退」与形态核**互相抵消**（本卡引入的回归）

`_ensure_vault_fingerprint_table` 的早退判据是 `_fingerprint_table_exists()` = **按名字**判存在；
`_looks_like_fingerprint_table` 是 **按 schema** 判形态。两个判据不同口径，于是：

vault `a_canvas` 用逻辑名 `file_fingerprints` 写内容 ⇒ 产生**带 `vector`** 的
`a_canvas_file_fingerprints` ⇒ 补建钩子看到「名字在」**恒早退**、永不建真指纹表；
形态核看到「带 vector」把 `a_canvas` **排除出 V** ⇒ 短 vault `a` 的自愈把
`a_canvas_nodes` 当自己的规范内容表删掉。

⚠️ **这是本卡引入的回归**，Codex 原话：「改前纯后缀反推会保留这里真实存在的 `a_canvas`，
新增形态核才移除了这层保护」。已接受的「配置错误终态」**不包含跨 vault 丢数据**。

### r2 的 2 条 LOW + 若干如实更正（登记）

- **LOW-1 说明未同步**：我改了行为却没同步 docstring / 日志 —— 缺列现在是保留却仍写「排除」；
  配置恰为 `file_fingerprints` 时会正常删除却仍写「必然 409」；`_ensure` 的「首次建表」说明
  落后于「每次成功写入都补建」。这正是 DD-13 名实一致，**应当修**。
- **LOW-2 诊断字段门可被截断文案绕过**：把原文换成 `"RuntimeError: [redacted]"`，
  现有子串断言仍过。当前实现无此回归，属门未覆盖的性质。登记。
- **我的第三条过强主张被更正**：「候选数 = vault 数」不成立 —— 候选数是**所有后缀匹配表数**。
  Codex 原话：「没有耗时证据，不能认定已成为瓶颈，也不能确认代价可忽略」。
- **五态不是整个操作的异常全集**：`:1607` 再次枚举待删列表若瞬时失败会直接抛出、不产生回执（既有边界）。
- **`initialize()` 先跑 `_cache_tables()`**，早于任何写入钩子 ⇒ **不能**无条件声称
  「任何破坏性路径之前指纹表必已建成」。

### r2 两条 HIGH 的处置（`1610f01b`）

**HIGH-B —— 两件事一起做**（单做任何一件都不够）：

1. `_ensure_vault_fingerprint_table` 的早退判据改成**与形态核同口径**：
   名字存在 **且** `_looks_like_fingerprint_table(fp_table)` 为真才算「已有」。
   名字被占但形态不符时**不建也不删**（建会撞、删会丢别人的数据），只 `logger.error`。
2. `_looks_like_fingerprint_table` 排除带 `vector` 的占名表时**同时置 `_vault_registry_degraded`**。

取 fail-closed 的理由：这张表说明「有个 vault 的归属判不出来」⇒ V 不可信 ⇒
drop 走闸① 整次拒绝、启动自愈整段跳过。

⚠️ **代价如实写进了代码注释**：任何带 `vector` 且名字以 `_file_fingerprints` 结尾的表会把
**整库**打成降级，于是**所有** vault 的删索引与维度自愈都停。这很重，但它可见
（`logger.error` + HTTP 409 `registry_degraded`），修法是改配置或改表名 ——
比静默删掉别人的表好。**这个取舍请主 session 复核。**

连带：M2 锁的终态从 `ambiguous` 改成 `registry_degraded`（闸① 现在先于闸④ 开火，
且更准确 —— 问题本来就是「V 不可信」，不是「某张表判不出主人」）。

**HIGH-A —— `rebuild_index` 返回前无条件补一次。**
**站点枚举**（避免只修一处）：`lancedb_client.py` 的 4 个 `drop_table` 里只有
`rebuild_index` 那处删**指纹表**（其余是内容表 / 漂移守卫 / `drop_vault_tables` 整删）；
`app/api/v1/endpoints/metadata.py` 的 `force_rebuild` 删的是
`resolve_table_name("vault_notes")` = 内容表。

**LOW-1 名实一致（DD-13）已修三处**：缺列改写「**保留**不排除」；配置恰为 `file_fingerprints`
写明「**没有** 409 终态，会正常删掉回 200」；`_ensure` 标题从「首次建内容表时」改成「幂等补建」。

### r3 的 1 HIGH + 3 LOW 的处置（`f6ea5006`）

**r3 HIGH：r2 HIGH-A 修得不彻底。** 我把补建放在 `rebuild_index` 的**正常返回路径**上，
Codex r3 指出它覆盖不到两件事：① `progress_callback` 抛异常 / 任务被取消会直接越过它；
② 即便最终会补，重建**期间**（`index_vault_notes` 要向量化，有 `await` 让出点）指纹表也是
缺的，另一个客户端此时跑 drop 或启动自愈就能认领这个 vault 的内容表。

修法比它提的更进一步，两件：

1. **删掉旧指纹表后立刻补一张空的** —— 把窗口压到最小。重建本就要清空指纹基线，
   空表正是它要的状态；随后 `_update_fingerprint` 走 `open_table` + `add`，行为等价。
2. **整个重建包 `try/finally`**，退出路径再补一次；`finally` 里那次补建自己再包一层
   `try/except Exception`，不让它的失败掩盖正在传播的异常。

**r3 LOW-1 已同步 6 处说明**。其中一条是**事实陈述写错了**：`DropVaultReport` 的 docstring
称「两个消费方零改动」，实际 `endpoints/index.py` 已改调 report，零改动的只有
`g29_dual_vault_canary.py`。这条不是措辞问题，是我把自己做过的事写反了。

**r3 LOW-2 / LOW-3 登记不阻断**：新门可被「表名换成占位字符串」的负控通过；
`partial` 终态（指纹表删成功、内容表删失败）也会留下「有内容、无指纹」——
那是**基线既有**的部分失败行为，但它否定了我在 `rebuild_index` 注释里写的完整性说明，
该说明已重写。

**r3 的其余更正我都接受**：
- 「所有 vault 都停」**不精确** —— default／空口径仍跳过降级闸，停的是所有 **scoped** vault。
- 性能代价要说完整：健康且 TTL 命中时，每次 scoped 成功写入多一次**全量表名枚举** +
  一次 `open_table`/读 schema；降级结果**不缓存**，两次指纹表名求值可能各自重扫目录与全部候选。
- 「只改回配置不会移除已有占名表，降级会持续」。

### ⚠️ 一个稳定的失效模式（值得单独记）

r1 的 M-3（"only bare scope"）、M-4（"有 409 终态"）、r2 的"候选数 = vault 数" ——
**三轮被指出同一类问题：我的主张比证据强**。它们的共同形态是我在 docstring 里
把「我设计时想的」写成了「它保证的」，而门并没有锁住那句话。
处置：本卡此后新写的每一句断言式 docstring，都要先问「这句话有门锁着吗？」，
没有就改成描述（"当前实现如此"）而不是保证（"必然如此"）。

---

## §九 追加轮次（2026-09-19，内部对抗审查后）— ⛔ 非 Codex 轮次

> 总账: `_bmad-output/审查/internal-adversarial-review-P1-2026-09-19.md`
> 依据: 根 CLAUDE.md 铁律 3「代码审查必须独立 Agent」。**不满足 D-15**。

### 本卡新增 commit

- `dcc9589e` **指纹表归属闸** —— 本卡引入缺陷的修复。
  `_ensure_vault_fingerprint_table` 的 docstring 要求「名字被占时不能建」，实现只核 schema
  形态、不核归属。vault `a` 与 `a_file` 并存时会建出归属 `a_file` 的表，新造两条改前
  不存在的破坏：① `DELETE /index/a` 永久 409 collision；② `DELETE /index/a_file` 销毁
  `a` 的指纹基线。门 `test_ensure_fingerprint_refuses_a_name_owned_by_another_vault`
  带控制组；负控 `negctl-2` 拆闸红 → `git show HEAD:` 还原 shasum 逐字节同 → 重新绿。

### 4-A 追加（Claude 已代验）

- ✅ 三个门文件 **95 passed**（改前 94 + 本轮新增 1），显式文件跑法、核过收集数
- ✅ `pyright app` = **0 errors, 80 warnings**（绝对路径 + `test -x` 自证，未用 `tail` 取末行）
- ✅ `ruff check` rc=0；`ruff format --check` 两文件 **rc=0**（本次无 `LEFTHOOK_EXCLUDE`）
- ✅ openapi.json `5e0f87b7..HEAD` 差异 **0 行**（卡文 (j)/判据 5）
- ✅ 地盘核 `7b511551..HEAD` 落白名单，验伪锚 = 2（去掉 exclude 多出 `_bmad-output/` 路径）
- ✅ 串行车道绑定（协议 §1）：P1-B 本卡 diff 面 vs HEAD 为空；验伪锚换 P1-C 文件非空
- ✅ `*.stderr*` tracked = 0；失败运行产物（`timeout` rc=127 那次）**未入库**

### 未证明追加（≥4）

7. 未证明本卡任一发现在**真 LanceDB 失败**下可复现（`drop_table` / `list_tables` 的真实失败未构造出）
8. 未证明 `edge_rationales` 永久 409 与别名 `vault_id` 假 404 在现网配置下的触发率（只做静态推演 + 机械验算）
9. 未证明内部 Agent 审查的覆盖面与 Codex 等价 —— 5 个视角由主 session 选定，非协议规定审查面
10. 未证明 `rebuild_index` 的 `try/finally` 兜底补建被任何门锁住（单拆它，指定门仍全绿）

### 台账待登记追加（≥4）

9. 本卡引入：闸① 爆炸半径 = 该实例上**所有 scoped vault**，且无产品内解除途径（待用户裁）
10. 本卡引入：同端点两个 409 语义与体形不同（resolver 的 `detail` 是 str，refusal 的是 dict）
11. 本卡引入：端点无异常边界 ⇒ 逃逸异常由 `CORSExceptionMiddleware` 把 `str(e)[:500]` 回进 body，脱敏不变量无执行面
12. 既有被提升成契约面：`edge_rationales` 不在 `_BUILTIN_LOGICAL_TABLES`；别名 `vault_id` 未归一化；r5-M2 实害未闭合（只换了 `refusal_kind`）
13. `partial` 仍留下「有内容表、没指纹表」（BLOCKER 降 HIGH，理由见总账 §三 B-2）

---

## §十 条件 (n) 结案 —— 以人审替代达成（用户 2026-09-19 授权）

⚠️ **非 Codex r4。** Codex 实况：r1/r2/r3 已真跑并逐轮整改；r4 因 `gpt-6-astra`
在当前 ChatGPT 账号返回 400 未能执行（实证 `evidence-lance-index-delete/codex-model-unavailable-20260919.md`）。
用户裁定「认人审替代，本批收口」，依协议 §1「主 session 人审替代，不等配额」先例。

裁定书：`_bmad-output/审查/CARD-LANCE-INDEX-DELETE-CONTRACT-人审裁定-r4替代-20260919.md`
（4 项重点核查全过，其中控制组有效性与调用方前提两项由注入/实测支撑；阻断级 = 0）

### ⛔ 不变量的已知例外（随裁定同步声明）

「scoped vault 写过内容表就必有指纹表」在**命名空间碰撞的 vault**（如 `a` 与 `a_file`
并存）上**有意不成立**。强行成立会让 `a` 建出归属 `a_file` 的表，造成
① `DELETE /index/a` 永久 409 collision；② `DELETE /index/a_file` 销毁 `a` 的指纹基线。
此类 vault 退回改前口径，**修法是改 vault id**，不在本卡范围 ⇒ 台账移交。

### 台账登记口径（⛔ 照抄，勿简写）

> P1-B 条件 (n)：**以人审替代达成**（用户 2026-09-19 授权），**非 Codex r4**。
> Codex 轮次实况 = r1/r2/r3。P1-C（CARD-G4-5）Codex 轮次 = **0**，同批同因，同以人审替代收口。
