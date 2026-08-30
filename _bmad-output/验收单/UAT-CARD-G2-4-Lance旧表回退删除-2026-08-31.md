# 验收单 — CARD-G2-4 Lance 旧表回退删除与显式归档

> **批次**: BATCH-2026-08-29-第七批 · 车道 V5 第一卡
> **日期**: 2026-08-31
> **worktree**: `.claude/worktrees/card-v5-lance`（未 push）
> **卡文锚点**: 总账 v2 §G2-4（计划书 L264 / L113 legacy vault_notes 读写共用回退 / L48「legacy 表 fail-open」）

---

## 一、这张卡给你带来什么（用户可感说明）

### 1. 「查不到自己的笔记，就去翻别人的」这条暗路被拆了

以前 LanceDB 的表名解析里有一条兼容回退（代号 B0.7）：当**你这个 vault 专属的表还没建**、
但库里存在一张**没有 vault 前缀的旧表**时，系统会**自动改去读那张旧表**。

它的问题不是"多读了点东西"，而是三件事同时发生：

1. **读**：vault A 查不到自己的表 → 读到旧表里 vault B 的笔记，而返回结果里**没有任何标记**
   能让你看出"这不是我的数据"；
2. **写**：同一条解析逻辑被 6 处索引/写入路径共用（`rebuild_index` / `index_image_content` /
   `index_canvas` / `index_vault_notes` / `index_single_file` / `add_documents`）—— 新 vault 第一次建索引时前缀表还不存在，
   于是**新数据被写进那张公共旧表**，跟别人的混在一起；
3. **重建**：`POST /index/vault?force_rebuild=true` 会先 drop"本 vault 的表"再重建 ——
   在同样条件下它 drop 的是**那张旧表**。也就是说旧代码里一次 force rebuild
   可以直接删掉历史/他人的数据（`metadata.py:567`）。

现在：非单 vault 部署下，表名解析**恒定**返回 `{vault}_表名`，三条路径全部只碰自己的表。

### 2. 「表没建」不再假装成「查了但没有」

以前表不存在时，检索层把异常吞成空列表，上层看到的是"检索正常，只是没命中"。
两种完全不同的情况长得一模一样：

| 你实际遇到的 | 旧系统告诉你 | 现在告诉你 |
|---|---|---|
| 这个 vault 压根没建过索引 | 「没有相关材料」 | `status=unavailable` + `reason=lancedb_table_missing: {表名}` |
| 索引在，但这次查询确实没命中 | 「没有相关材料」 | `status=empty`（不变） |
| 索引在，查询过程炸了 | 「没有相关材料」 | `status=unavailable` + `reason=search_failed: …`（不变） |

对你的实际意义：第一种情况的下一步动作是**跑一次索引**，第三种是**看后端日志**——
以前这两件事被压成同一句"没有材料"，只能靠猜。

### 3. 单 vault 部署没有被误伤（这是刻意保留的）

如果 `vault_id` 是 `default` 或空（单实例部署），无前缀表**就是**它的正常命名空间，
读写照旧。这条映射被两处判据钉死，防止后人"顺手清理"时把单 vault 部署炸掉：
`tests/unit/test_lancedb_vault_isolation.py:23` / `:35`，以及本卡新增的真库对照
`test_default_vault_still_maps_to_bare_table` / `test_default_vault_write_still_targets_bare_table`。

---

## 〇、一条输入缺口（如实声明）

卡文首句写「**必读：手册 §二 两卡要点**」。本批次（第七批）的开跑手册**在仓库里不存在** ——
`_bmad-output/implementation-artifacts/goal-cards/` 下最新的是
`2026-08-29-第六批开跑手册-6车道7卡.md`；我在主仓、各 worktree、以及所有
2026-08-30 之后修改过的 md 里都搜过 `G2-4`，没有第七批手册。

所以我按以下替代真相源执行，并在此声明以便你核对我是不是漏了要点：

1. **卡文本身**（`/goal` 全文，条款极详细，(a)-(d) 逐条可判）；
2. **总账 v2 §G2-4 / §G2-5 逐卡档案**（`2026-08-28-主goal全量分goal总账-v2.md:439-460`）；
3. **第六批手册 §三 的公共纪律**（codex 命令加 `</dev/null`、commitlint 长度、
   guard-hook 拦 rm 用 mv、不 push、live vault 与 Neo4j 7691 只读、
   `exam_service.py`/`verification_service.py` 归 G5-12 禁改）。

若第七批手册确实存在于我看不到的地方，请把 §二 给我，我照它复核一遍。

---

## 二、完成条件逐条对账

| 卡文条款 | 状态 | 证据 |
|---|---|---|
| (a) 删 `lancedb_client.py` B0.7 回退分支 | ✅ | `resolve_table_name` 现为纯前缀拼接（`lancedb_client.py:762-793`）；行为门 `test_prefixed_missing_no_longer_falls_back_to_bare` |
| (a) 保留 `vid=="default"`/空 → 裸表映射 | ✅ | `test_lancedb_vault_isolation.py::TestResolveTableName` 5 passed（含钉死的 :23/:35）+ 真库对照 2 条 |
| (a) 引入 `TableMissingError` 类型化异常 | ✅ | `lancedb_client.py:86-115`（继承 `RuntimeError`，理由见下 §三.1） |
| (a) 只让表缺失穿透 catch-all，其余维持旧契约 | ✅ | `search()` 新增 `except TableMissingError: raise` 置于两条 catch-all 之前；反向对照 `test_table_missing_penetrates_enable_fallback_swallow_gate`（同一测试里证明"别的异常仍被吞成 []"） |
| (a) 表缺失透出 degraded/unavailable + 非空 reason（复用 ServiceStatus） | ✅ | `search_supplementary` 返回体新增 `status` 字段取 `ServiceStatus` 值域；`test_search_supplementary_surfaces_unavailable` |
| (b) 删 tier-2 裸表直开分支与 env 闸 | ✅ | `_two_tier_search`→`_vault_scoped_search`（单层）；`_enable_tier2_fallback` 删除；grep 门 G3 |
| (b) 重写对应测试 | ✅ | `TestTier2FallbackGate`→`TestTier2BranchRemoved`（5 条删除锁）；`TestTopLevelDegradedFromLegacyFallback`→`TestLegacyFallbackDegradedPathRemoved`（4 条） |
| (c) 迁移工具＝归档器（g23 骨架 + dry-run 零写入 + hash/count 对账） | ✅ | `backend/scripts/archive_legacy_lance_tables_g24.py`；行为门 **15 条**（含 round-1 六条硬伤的回归锁）。对账已从 `str()` 弱指纹升级为 Arrow schema + 类型化内容指纹；归档落 **DB 目录之外**的 Parquet |
| (c) 现网 dry-run 预期零动作 | ⚠️ **卡文预期与实测不符** | 见 §四.1 —— 现网**有** 1 张裸表 |
| (d) grep 门三条 | ✅（G3 有一条枚举豁免；G2 升级为 AST + 棘轮） | `backend/scripts/g24_grep_gate.sh` rc=0；豁免理由见 §三.3，棘轮基线见 §七 |
| (d) tmp 库行为测试（读侧 + 写侧） | ✅ | `tests/unit/test_g24_lance_legacy_table_removal.py` **10 passed**（真 LanceDB，不 mock 存储层） |
| (d) `-k "lancedb or supplementary"` 与基线 comm 零新增失败 | ✅ | baseline 13 failed/140 passed → after 13 failed/141 passed；`comm` 双向差集为空 |

### 判据命令与结果

```
$ bash backend/scripts/g24_grep_gate.sh                      → rc=0（三条判据 + 三次正向对照自检 + 扫描面存在性校验）
$ .venv/bin/pytest -k vault_doc_roles                                    → 119 passed（BLOCKER-3 刷新 SHA 后）
$ .venv/bin/pytest tests/unit/test_g24_lance_legacy_table_removal.py    → 10 passed
$ .venv/bin/pytest tests/unit/test_archive_legacy_lance_tables_g24.py   → 15 passed
$ .venv/bin/pytest tests/unit/test_supplementary_search_service.py      → 55 passed
$ .venv/bin/pytest tests/unit/test_lancedb_vault_isolation.py           → 3 failed(基线同款) / 28 passed
$ .venv/bin/pytest tests/unit -k "lancedb or supplementary"             → 13 failed / 141 passed
    ↳ comm 对账: 新增失败 0 条, 消失失败 0 条（失败集合与基线逐字相同）
```

**基线 13 条既存失败**（与本卡无关，改动前后逐字相同）：`test_chat_endpoint.py` 1 条 +
`test_lancedb_vault_isolation.py` 3 条 + `test_supplementary_reranker.py` 9 条。

### 更宽的回归面（全部与 HEAD 逐条对照过，非"看名字像是旧的"）

对照方法：`git worktree add --detach <tmp> HEAD` 拉一份**未改动**的树，拷 `.env` 后用同一个
venv 跑同样的命令 —— 这样"这条失败是不是我弄的"有实证，而不是靠推断。

| 套件 | 本树 | HEAD 树 | 结论 |
|---|---|---|---|
| `tests/regression`（全量） | 5 failed / 991 passed | 同样这 5 条（`test_search_error_memories` 3 + `test_write_side_group_guard` 2） | 零新增 |
| `tests/integration/test_multi_vault_isolation.py` | 4 failed / 8 passed | 同样这 4 条 | 零新增；`test_lancedb_resolve_table_name_per_request_vault` **通过** |
| `tests/regression/test_rag_stage1_index_contracts.py` | 35 passed / 0 failed | — | 索引契约未被波及 |
| `-k multimodal`（unit+regression） | 5 failed / 80 passed | 同样这 5 条 / 79 passed | 零新增（80 vs 79 = 本卡新增的守卫测试） |

### 存量测试适配逐条记录（卡文 (d) 明写要求「预计 5-8 个存量测试需适配，逐一记录」）

实际适配 **6 个文件**（落在预估区间内），每条都注明"为什么非改不可"——凡是
"删掉断言让它变绿"的都不算适配，下表每一条要么是被测行为真的没了，要么是原断言
本身证伪：

| # | 文件 | 改了什么 | 为什么非改不可 |
|---|---|---|---|
| 1 | `tests/unit/test_supplementary_search_service.py` | `TestTier2FallbackGate`（6 条）→ `TestTier2BranchRemoved`（5 条）；`TestTopLevelDegradedFromLegacyFallback`（3 条）→ `TestLegacyFallbackDegradedPathRemoved`（4 条） | 原来锁的是"env 开关默认关"与"tier-2 命中时顶层翻 degraded"。**被锁的行为整个删除了**，所以不是改断言，是换成**删除锁**（断言开关与旧函数名不存在、env 设 true 也不碰 `client._db`） |
| 2 | `tests/regression/test_rag_stage2_chain_unify_contracts.py` | monkeypatch 目标改名；删一处 `delenv`；`test_tier1_vector_fallback_excludes_exam_board` → `test_vector_fallback_excludes_exam_board`；**新增** `query_type` 值序列断言 | 函数改名（DD-13）必须同步；`delenv` 的对象已不存在；新增的值断言是 Codex MEDIUM-2 抓出的——原断言只数调用次数，在"回退其实又跑了一次 hybrid"时照样绿 |
| 3 | `tests/regression/test_rag_stage2_rerank_contracts.py` | `test_dedup_merges_taint_fail_closed` 去掉 `is_legacy_fallback` 那半边断言 | 该字段**全仓唯一生产者**（tier-2）已删，继承逻辑随之移除。taint / injection_risk 的 fail-closed 语义**原样保留**并仍被断言 |
| 4 | `tests/regression/test_rag_stage2_t6_verification_contracts.py` | monkeypatch 目标改名 | 同 #2 的改名连带 |
| 5 | `backend/scripts/vault_doc_roles.yaml` | G4-16 登记的「Tier-2 旁路」边界描述改为"已关闭" | 台账里那条边界随分支删除而失效，不改台账就在说谎 |
| 6 | `backend/scripts/check_vault_doc_roles.py` | `ROLES_SHA256` 刷新 | #5 改了 yaml 就必须同步这个强制指纹，否则 `test_vault_doc_roles.py` 在 setup 直接 `ConfigError`。**这条是 Codex BLOCKER-3 替我抓到的，我自己漏了**（我的 `-k` 选择面没覆盖它） |

**零"降低门槛"式适配**：没有任何一条是通过放宽断言、加 `xfail`、或缩小参数化范围
让测试变绿的。

---

## 三、设计决定与它们的代价（如实）

### 1. `TableMissingError` 继承 `RuntimeError`，不是裸 `Exception`

`search()` 有 6+ 类调用方，其中 `react_agent.py:99` / `:108`（`search_vault_notes` 的两级 except）只捕
`(RuntimeError, ConnectionError, ValueError)`。若新异常不继承 `RuntimeError`，
它会从这些窄捕获里逃逸成未捕获异常（在 agent tool 层炸出去）。继承之后：

- 既有窄捕获**零改动**仍能兜住（行为不劣于改动前）；
- `search()` 内部按类型精确放行，使它**唯一地**穿透 `enable_fallback` 吞噬门；
- 代价：`search_supplementary` 里 `except TableMissingError` **必须**排在
  `except (RuntimeError, …)` 之前，顺序写反会让表缺失重新塌缩成 `search_failed`。
  这条约束已写进代码注释，并由 `test_table_missing_reason_is_distinguishable_from_search_failed` 锁住。

### 1.5 异常穿透后的全链落点（逐条核过，不是推断）

| 调用方 | 原行为（表缺失时） | 现行为 | 是否需要改代码 |
|---|---|---|---|
| `supplementary_search_service._vault_scoped_search` | 吞成 `[]`→`empty_index` | 上抛 | 已改（本卡） |
| `search_supplementary` | `empty_index`（degraded=False） | `unavailable` + 专属 reason | 已改（本卡） |
| `note_search_tools._fast_path_search`（MCP，`enable_fallback=False`） | `ok_empty` 假成功 | `degraded && not materials` → `raise RuntimeError("supplementary search degraded: lancedb_table_missing: …")` → 外层 `search_notes` 报 `source_status="error"` | **不需要**（既有分支天然接住） |
| `react_agent.search_vault_notes` | `[]`→"[No results]" | 两级 `except (RuntimeError, …)` 接住 → `[Error] Search failed: …` | **不需要**（继承 `RuntimeError` 的收益） |
| `VaultNotesService.search`（lib retriever） | `[]` | 仍是 `except Exception → []`，**表缺失照旧被吞成空** | **不需要**（行为不变）；但这条路径上「表没建」依旧伪装成「没命中」——**本卡未覆盖**，见 §六 FU-1 |
| `multimodal_retriever`（LangGraph 节点） | `[]` | 外层 `except Exception` 接住 | **不需要** |
| `multimodal_store` 四个读方法 | **本来就抛 `TypeError`**（签名错位，见 §三.6） | 不变（异常在到达表缺失判定前就抛了） | **不需要**；真问题登记 FU-5 |

### 2. `_two_tier_search` 改名 `_vault_scoped_search`（DD-13）

tier-2 删除后只剩一层，旧名即名不符实。**不保留别名** —— 留个 alias 会让"还有两层"的
错觉继续传播。波及 3 个 regression 测试文件的 monkeypatch 目标 + 2 处注释，已同步。

### 3. grep 门 G3 的枚举豁免（与卡文"全仓 0 命中"的偏差，明写）

卡文要求 `ENABLE_LANCEDB_TIER2_FALLBACK` **全仓 0 命中**。实际保留了两类命中：

| 豁免 | 理由 |
|---|---|
| `_bmad-output/` `_archive/` 等历史存档 | 存档记录的是当时的事实，改写存档＝篡改证据 |
| `backend/tests/unit/test_supplementary_search_service.py` | 删除锁测试必须写出开关名才能断言"它已经没了"。不写只能靠拼字符串混淆，那才是坏味道 |

门对第二类做了**收紧断言**：该文件里出现该字符串的行，必须全部落在删除锁测试类
`TestTier2BranchRemoved` 之内（或自称"删除"的说明行），否则判红。
活代码侧我把注释里的开关名也去掉了（改为指向本验收单），因此 `backend/app` `backend/lib`
`backend/scripts` `config` `docker` 全部 0 命中。

### 4. `is_legacy_fallback` 字段的连带清理

tier-2 是该字段在全仓的**唯一生产者**。删除后它的 4 处消费分支全部不可达，
留着会让人以为"还有 legacy 告警能力"（实际永远不响）。已在
`supplementary_search_service.py` 内清理干净，并同步更新 1 条 regression 断言。

**未清理（登记移交）**：`backend/app/mcp/tools/note_search_tools.py:286/:297` 的
`signal_keys` 元组里仍列着该字段名。它是 `{k: m[k] for k in signal_keys if m.get(k) is not None}`
形态的投影白名单，字段永不出现即永不投影 —— **零行为影响**，但字面已陈旧。
该文件不在本车道独占清单内，故只登记不改。

### 6. 我曾越界改 `multimodal_store.py`，**已全部还原**（连同我的错误判断一起纠正）

审查过程中我给 `backend/lib/agentic_rag/storage/multimodal_store.py` 加过一个
`_search_rows()` 守卫，理由写的是"不加的话本卡会给这条路径新增 500"。

**这个理由是错的。** Codex round-1 MEDIUM-3 指出并经我实证复现：

```
$ python -c "... asyncio.run(c.search(table_name='multimodal_content', query_vector=None, filter={...}, limit=1))"
TypeError: LanceDBClient.search() got an unexpected keyword argument 'query_vector'
```

`LanceDBClient.search()` 的签名里**根本没有** `query_vector` / `filter` / `limit`
这三个参数（只有 `query/table_name/canvas_file/subject/num_results/metric/query_type/
course_id/tags/rrf_k/doc_type/exclude_doc_types`）。也就是说 `multimodal_store` 的
四个读方法**在本卡之前就已经必抛 `TypeError`** —— 它们从来没有"静默返回空"过，
我说的那个"新增 500"并不存在，而我加的守卫因为异常在到达它之前就抛出了，
**永远不可能被执行**。

处置：整段还原（`git diff` 对该文件为空），连同那条不可达的测试一并删除。
真正的问题（多模态读路径的签名错位）作为 **FU-5** 登记，不在本卡射程。

**教训记在这里**：我当时是从"调用点没有 try 包裹"推断出"会新增 500"的，
没有真的去比对被调函数的签名。一个没验证过的前提，撑起了一次越界改动。

---

## 四、实测发现（卡文预期之外）

### 1. ⚠️ 现网**有**裸表 —— 卡文的「现网无裸表→dry-run 预期零动作」只对了一半

只读普查（`docker exec canvas-learning-system-backend`，`/lancedb`，2026-08-31）：

| 表 | 分类 | 行数 | 备注 |
|---|---|---|---|
| `canvas_vault_vault_notes` | vault-scoped | 2203 | 唯一活笔记表 |
| `canvas_vault_file_fingerprints` | vault-scoped | 64 | |
| **`file_fingerprints`** | **bare_legacy** | **77** | **裸表，mtime 2026-05-09** |

- 卡文对的一半：裸 `vault_notes` **确实不存在**。
- 卡文错的一半：裸 `file_fingerprints` **存在，77 行**，schema 与 vault 版逐列相同
  （`file_path` / `content_hash` / `last_indexed` / `chunk_count`），是 RAG-S1 F1 分表前的旧副本。

因此归档器现网 dry-run **不是零动作**：`pending_count=1`，`exit 2`（＝需人工裁定，与 g23 同语义）。
证据里还留下一条 HIGH-2 的实锤：现网 `ACTIVE_VAULT` 的原始值是 `canvas-vault`（连字符），
经应用 sanitizer 归一后才是 `canvas_vault` —— 归档器现在用的正是应用那套归一化。
证据 JSON：`_bmad-output/审查/evidence-g24/live-lancedb-census-2026-08-31.json`。
运行前后 `/lancedb` 目录三张表的 mtime 逐字未变（dry-run 零写入）。

**这张裸表当前是不是活的？** 指纹表路径 `_fingerprint_table_name`（`lancedb_client.py:959`）
本来就**刻意没有** B0.7 回退，所以对 `vault_id != default` 它已经是孤儿；只有单 vault 部署
（`default`/空）才会读写它。本卡不动它 —— 需要你裁决（见 §六）。

### 2. 顺手关掉的一个数据销毁面（本卡副产品）

`metadata.py:567` `force_rebuild` 分支：`drop_table(resolve_table_name("vault_notes"))`。
在"前缀表不存在 + 裸表存在"这一 B0.7 触发条件下，它 drop 的是**裸表**。
删除回退后它只可能 drop 自己的前缀表。此前未见有人点名过这条路径。

### 3. schema-drift 自动 drop 与裸表的交互（首跑实测踩到）

`_check_and_fix_dimension_mismatch`（`lancedb_client.py:3584`）在写入时若发现目标表
**缺 `doc_type` 列**（RAG-P0 之前的表都缺），会 **drop 并重建**该表。
含义：单 vault 部署（`default`）下，一次写入就会把缺列的裸表整张重建（旧行丢失）。
这是既有行为、与本卡无关，但与"裸表还有没有数据"直接相关，登记在此备查。
本卡的行为门 fixture 因此显式种了 `doc_type` 列，避免归因失真。

---

## 五、变更清单

**改动（10 文件）**
- `backend/lib/agentic_rag/clients/lancedb_client.py` — 删 B0.7；加 `TableMissingError` + `_is_table_absent`；`_search_internal` 分流；`search()` 放行
- `backend/app/services/supplementary_search_service.py` — 删 tier-2 分支与 env 闸；`_two_tier_search`→`_vault_scoped_search`；表缺失专属降级档 + `status` 字段；清理 `is_legacy_fallback` 死分支
- `backend/app/api/v1/endpoints/chat.py` / `backend/app/mcp/tools/note_search_tools.py` — 注释里失效的旧函数名改正 + 删除已无生产者的 `is_legacy_fallback` 投影字段（Codex LOW-2）
- `backend/scripts/check_vault_doc_roles.py` — `ROLES_SHA256` 随 yaml 改动刷新（Codex BLOCKER-3）
- `backend/scripts/vault_doc_roles.yaml` — G4-16 登记的「Tier-2 旁路」边界已关闭，描述同步
- `backend/tests/unit/test_supplementary_search_service.py` — 两个测试类重写为删除锁
- `backend/tests/regression/test_rag_stage2_{chain_unify,rerank,t6_verification}_contracts.py` — monkeypatch 目标改名 + 1 条 legacy 断言随字段删除

**新增（4 文件）**
- `backend/scripts/archive_legacy_lance_tables_g24.py` — 归档器（census / pending / --apply，默认只读）
- `backend/scripts/g24_grep_gate.sh` — grep 裁判门（含正向对照自检）
- `backend/tests/unit/test_g24_lance_legacy_table_removal.py` — 真库行为门 9 条
- `backend/tests/unit/test_archive_legacy_lance_tables_g24.py` — 归档器行为门 7 条

---

## 六、待你裁决（⛔ 不自作主张）

> 两卡的裁决点已集中到 `_bmad-output/验收单/裁决点汇总-车道V5-G2-4与G2-5-2026-08-31.md`（编号 D1-D7），
> 该文件同时写明「为什么这些必须由你决定、我不自行执行」。下面是本卡这一半的原文。

1. **现网裸 `file_fingerprints`（77 行）怎么处置**
   - 甲：归档（复制到 `_g24archive__file_fingerprints__{ts}` 后 drop 原表）—— 需先把 volume 做隔离副本，
     `--apply` 对现网路径硬拒绝，不会就地执行；
   - 乙：原地留着不动（它对多 vault 已是孤儿，只在单 vault 部署下才被读写）；
   - 丙：现在只登记，等 G2-9 双 vault 隔离 canary 一起收。
   （我的建议：**丙** —— 它不在任何在线读路径上，且 G2-9 要重新盘点整个数据面。）

2. **`note_search_tools.py` 里陈旧的 `is_legacy_fallback` 字段名**：补一个 micro-patch 清掉，
   还是等该文件所属车道顺手带走？（零行为影响，纯字面陈旧。）

3. **`edges.py` 的裸表直写**（FU-4）：AST 门照出 `open_table("edge_rationales")` /
   `create_table("edge_rationales")` 两处**写侧**直开裸表，与本卡删掉的 B0.7 同型
   （跨 vault 写混）。它不在本车道文件面内，我只钉了棘轮基线没有改。要不要单开一张卡？

4. **grep 门 G3 的枚举豁免**（§三.3）是否接受 —— 若你坚持字面「全仓 0 命中」，
   我就把删除锁测试里的开关名也去掉，代价是那条最强的回归锁（"env 设成 true 也不碰裸表"）
   要降级成只断言 `_enable_tier2_fallback` 不存在。

---

## 六.5、遗留（登记，不在本卡射程）

- **FU-1 `VaultNotesService.search`（`vault_notes_retriever.py:250-254`）仍把表缺失吞成 `[]`**，
  其 docstring 甚至写着"table may not exist yet"。也就是说本卡把 supplementary/MCP 链的
  「故障伪装成空」修好了，**LangGraph 检索节点这条链没修**。卡文只要求 supplementary 链透出，
  故本卡不动它——但"四态贯穿全链"归 G4，这条应进 G4 的清单。
- **FU-2 `note_search_tools.py` `signal_keys` 里陈旧的 `is_legacy_fallback`**（零行为影响，见 §三.4）。
- **FU-4 `edges.py` 写侧裸表直开**（`open_table`/`create_table` 各一处，
  绕过 `resolve_table_name`，跨 vault 写混面）—— 已钉进 grep 门的棘轮基线。
- **FU-5 多模态读路径签名错位**：`multimodal_store` 的 4 个读方法用
  `query_vector/filter/limit` 调 `LanceDBClient.search()`，而该方法没有这些参数 →
  **必抛 `TypeError`**（本卡实证）。这条链事实上是坏的，与本卡无关但值得单独裁定。
- **FU-6 `react_agent` 对表缺失的诊断退化**：typed 异常被当成普通 `RuntimeError`，
  会对同一张不存在的表再查一次，最后给出 generic `[Error]`，原有的"尚未索引，请跑
  index/vault"提示反而不可达。
- **FU-3 `_search_internal` 开头的 `if self._db is None: return []`** 仍是同一类 fail-open
  （LanceDB 根本没连上 → 返回空，与"真没命中"同形）。它不是 legacy 表回退，不在本卡射程；
  但它与本卡修的是同一种病，应与 FU-1 一起进 G4 的四态贯穿清单。

---

## 七、Codex 审查与整改

存档：`_bmad-output/审查/codex-review-CARD-G2-4.md`。
Round 1 判 **FAIL**（3 BLOCKER / 3 HIGH / 6 MEDIUM / 2 LOW）。我先逐条**实证复核**了它的
事实主张（不照单全收），结论是**全部属实**，其中三条直接推翻了我自己的判断。

| 级别 | 问题 | 我的复核 | 整改 | 回归锁 |
|---|---|---|---|---|
| BLOCKER-1 | `file://` 双解释绕过 live 拒绝闸（闸按普通路径解析、`lancedb.connect` 按 URI 解析） | 属实 | `canonical_db_path()` 一律拒绝带 scheme 的写法，同一个 `Path` 同时交给闸与 connect | `test_uri_db_path_is_refused` |
| BLOCKER-2 | 归档副本留在同一个 LanceDB 里，会被后端启动的 schema 自愈 drop（源表与归档双双消失） | 属实——`_cache_tables()` 对每张非指纹表跑 `_check_and_fix_dimension_mismatch()`，缺 `doc_type` 就 drop | 归档改为导出到 **DB 目录之外**的 Parquet + 回读核对后才 drop | `test_archive_survives_client_schema_repair`（跑**真实**的 `_cache_tables()`，并用一张同样缺 `doc_type` 的前缀表做正向对照证明它真的会删） |
| BLOCKER-3 | 改了 `vault_doc_roles.yaml` 却没刷新 `check_vault_doc_roles.py` 的强制 SHA → 既有测试红 | 属实，我完全漏了（我的 `-k` 选择面没覆盖它） | `ROLES_SHA256` 刷新为 `2a68d4cd…` | `-k vault_doc_roles` 119 passed |
| HIGH-1 | `str()` 指纹把 `1` 与 `"1"` 判成相同，对账"通过"后就删源表 | 属实 | 指纹改为 Arrow schema + **类型化**单元格（`type(v).__name__` + `repr`），schema 也参与对账 | `test_digest_is_type_sensitive`（含"真相同必须同指纹"的正向对照） |
| HIGH-2 | 未复用应用的 `sanitize_vault_id`，`ACTIVE_VAULT="Default"` 会被判成多 vault → 误删正常裸表 | 属实 | 只接受 `app.config.sanitize_vault_id`，导不到就 fail closed | `test_capitalized_default_is_single_vault`；现网证据里 raw `canvas-vault` → canonical `canvas_vault` 正是这条 |
| HIGH-3 | 白名单漏表（`canvas_explanations` / `edge_rationales`）→ 真受影响的裸表被报成 clean | 属实 | 补全表名契约；**契约外的裸表不再等于干净**，进 `unknown_bare` + exit 2 | `test_unknown_bare_table_is_pending_not_clean` |
| MEDIUM-1 | `table_names()` 默认 `limit=10`，`_is_table_absent` 会把第 11 张之后的表判成不存在 | 属实（lancedb 0.30.2 签名实查） | 新增 `_all_table_names()` 走 `list_tables(limit=None)` | `test_is_table_absent_sees_past_default_pagination`（含"默认确实只给 10 张"的前提断言） |
| MEDIUM-2 | 所谓 vector-only 回退其实又跑了一次 hybrid（`search()` 默认 `query_type="hybrid"`） | 属实，且是**旧代码就有**的名实不符 | 回退分支显式传 `query_type="vector"` | 单元 + regression 两处都改成断言**值**序列 `["hybrid","vector"]`，不再只数调用次数 |
| MEDIUM-3 | 我加的 multimodal 守卫在生产客户端上不可达（签名错位） | 属实，实证复现 `TypeError` | **整段还原**，连测试一起删；真问题登记 FU-5 | — |
| MEDIUM-4 | `search_multiple_tables` / `VaultNotesService` 仍把表缺失吞成空 | 属实 | 本卡不改（超射程） | 登记 FU-1 |
| MEDIUM-5 | `--out` 落进 DB 树破坏零写入；多表 apply 部分执行 | 属实 | `--out` / `--archive-dir` 在 DB 树内即拒绝；apply 改两阶段（全部导出核对通过才统一 drop） | `test_out_inside_db_tree_is_refused` / `test_archive_dir_inside_db_tree_is_refused` / `test_apply_aborts_without_dropping_when_reconciliation_fails` |
| MEDIUM-6 | grep 门自身 fail-open（路径不存在也报 0 命中 / 只抓双引号 / 类区间靠行号大小 / mktemp 失败继续跑） | 属实 | 扫描面先验存在可读；grep `rc>1` 判红；G2 改 **Python AST**；G3 用真实类区间；mktemp 失败即红 + trap 清理 | 门自身的三次正向对照自检 |
| LOW-1 | react_agent 对表缺失的诊断退化成 generic `[Error]` | 属实 | 本卡不改（超射程） | 登记 FU-6 |
| LOW-2 | `chat.py` / `note_search_tools.py` 仍引用旧名与旧字段 | 属实 | 注释改名 + 删除 2 处已无生产者的 `is_legacy_fallback` 投影字段 | grep 复核 |

**硬化后的门顺带照出一条新的存量缺陷**：AST 门（比原本的字面量 grep 强）在
`backend/app/api/v1/endpoints/edges.py` 抓到两处**写侧**裸表直开
（`open_table("edge_rationales")` / `create_table("edge_rationales")`），完全绕过
`resolve_table_name` —— 与本卡删掉的 B0.7 同型。不在本车道文件面内，故钉成
**棘轮基线**（新增一处即判红）+ 登记 FU-4，见 §六 裁决点 3。

**流程教训（如实记）**：我在 Codex 跑着的时候还在改代码，导致它反复重读工作区、
并在报告里专门声明"审查期间工作区发生过并发修改"。发起审查后应当冻结改动。
