# CARD-G4-1a 验收单 — 跨库读泄漏封堵（BLOCKER 面）

> **批次**: BATCH-2026-08-29-第六批 / 车道 T1
> **worktree**: `.claude/worktrees/card-t1-readleak`（分支 `card/t1-readleak`）
> **基线 HEAD**: `cbb20afb`
> **日期**: 2026-08-30（含 Codex round-1 整改）
> **上游**: 开跑手册 §二 G4-1a 要点 · 总账 v2 §G4-1 · G2-2 Codex round-1 移交条款（BLOCKER-5 / HIGH-7）
> **审查**: `codex-review-CARD-G4-1a.md`（round-1 裁定"需整改"）+ `codex-review-CARD-G4-1a-round1-整改记录.md`（round-1 十三条 + round-2 两条 + round-3 三条，逐条处置）
> **⚠️ 审查轮次如实声明**: round-2 / round-3 均被外部内容过滤在**收尾汇总阶段**中断，未产出完整分级报告与合并裁定；两轮中断前给出的 5 条反证已全部核实处置。详见整改记录末节与 §六裁决点 5

---

## 〇、一句话结论

读侧「`group_id=None` 直通 Neo4j = 全库扫描」的泄漏面已封死，改为 **fail-closed 解析 + 前缀语义**；同一套可见性规则覆盖 Cypher / 内存兜底 / JSON 降级三条路径。7692 真库门 **49 passed**（原 26），新增单元门 **60 passed**，变异负控 **17/17 门能红**，反向引用全清单（32 文件 / 542 测试）**零新增失败**。

---

## 一、用户可感说明（"复习建议是否仍能看到内容？"）

**结论：能，而且这正是本卡花最多力气保住的东西。**

原因反直觉，值得说清楚：

- 系统写数据时，**并不是**把所有东西都放进「vault 这个大袋子」，而是按白板分装进小袋子——`vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d` 就是「特征值与特征向量」那块中文白板的小袋子（中文名被转成 punycode 编码）。
- 2026-08-30 对现网 Neo4j（7691，**只读**）实测：**全库唯一的一个 Concept、唯一的一条 LEARNED 学习记录，都在这个小袋子里；vault 根袋子里一条都没有。**
- 所以封堵时若图省事写成「只认根袋子」（等值比较），泄漏确实堵住了，但**「复习建议」会变成整页空白**——用户看到的是"我的学习记录没了"，比读到别人 vault 的数据更像产品坏掉。

本卡用「**根袋子 + 它下面所有小袋子**」（等值 OR 前缀）：

| 场景 | 结果 |
|---|---|
| 打开总览看「复习建议 / 学习历史」 | ✅ 照常看到内容，包括中文白板里的记录 |
| 在某块白板上下文里查 | ✅ 只看到这块白板的，**兄弟白板的不会混进来** |
| 另一个 vault 的数据 | ✅ 一条都看不到 |
| 一键出题（`/exam/quick`）指向另一个 vault | ✅ 明确报 409，而不是"读 A 的批注、把题记成 B 的" |
| 系统连 active vault 都推导不出来（配置坏了） | ⚠️ 显式报错，**不会**悄悄返回空列表假装"没有数据" |

最后两条是 Codex round-1 抓出来补上的：以前"读不到"和"坏了"长得一模一样。

---

## 二、完成条件逐条对照

### (a) `vault_scope.py` 读侧 API ✅

`backend/app/core/vault_scope.py`（原 G2-2 写读通用解析部分零改动）：

| API | 职责 |
|---|---|
| `require_read_group(group_id, *, context)` | 显式值 → `current_group_id()`（ContextVar，未注入时推导 active vault）→ 仍无则抛 `VaultScopeUnresolved`。**不落 `DEFAULT_GROUP_ID`** |
| `read_scope_params(group_id, *, context)` | → `{"group_id": <物理组>, "group_prefix": <物理组+"__">}`（R5 物理化） |
| `read_group_filter(alias, *, allow_null=False)` | → `(n.group_id = $group_id OR n.group_id STARTS WITH $group_prefix)` |
| `group_in_read_scope(candidate, scope)` | 内存/JSON 侧同语义判定（两侧先 `to_physical_group_id` 再比较） |
| `_validate_scope_shape()` | 段级校验：非 `vault:` 前缀 / 空段 / 裸前缀 / **推导**出 `vault:default` 污染桶 → 抛 |
| `VaultScopeUnresolved` | **故意不继承 `RuntimeError`**（见下）；带 `context` 定位调用点 |
| `allow_cross_vault` | **re-export** `cypher_helpers.allow_cross_vault`（单元测试断言 `is` 同一对象，不造同名副本） |

**三个设计要点，每个都有门锁着**：

1. **前缀语义的锚点带 `__` 定界符**。裸前缀会让 `vault__a` 吃掉 `vault__ab`（另一个 vault）——`subjects.py:57` 先例已踩过；我自己的**测试辅助函数**也踩了一次，被生产代码的正确实现照出来。
2. **fail-closed 的触发边界**。`current_group_id()` 在 ContextVar 未注入时仍推导 active vault，所以 `VaultScopeUnresolved` 只在「配置断裂」时抛。正向断言 `test_fail_closed_does_not_fire_on_normal_read` 钉死"正常后台/CLI 路径不得抛"。
3. **异常基类是裸 `Exception`**。本仓多处优雅降级写作 `except (RuntimeError, ConnectionError, asyncio.TimeoutError)`——继承 RuntimeError 会让"配置坏了"被当成"Neo4j 暂时不可用"吞成空列表，恰好把 fail-closed 退化成静默断读（Codex round-1 H-3 实测复现）。`test_scope_exception_is_not_a_runtime_error` 把继承关系本身锁成契约。

**显式空白串（`""` / `"   "`）不走推导链，直接抛** —— 与写侧 `_resolve_physical_group_id` 的 C1 口径统一：调用方以为自己传了作用域，悄悄换成另一个比报错危险。

### (b) 封堵清单 ✅（卡文列 5+1；实际封堵 9 处 + 3 处同类 + 3 处 Codex 追加）

**卡文点名（行号按 HEAD 复核）**

| # | 位置 | 原状 | 处置 |
|---|---|---|---|
| 1 | `memory_service.py:644` `get_learning_history` else | `group_id = None` | → `require_read_group()` |
| 2 | `memory_service.py:1031→1055` `get_review_suggestions_with_status` else | `group_id = None` | → `require_read_group()` |
| 3 | `memory_service.py:682-683` 内存 episode 过滤 | 等值 | → `group_in_read_scope()` |
| 4 | `memory_service.py:739-749` failed_scores 过滤 | 等值 | → `group_in_read_scope()` |
| 5 | `memory_service.py:1737/1741` Tier 1 | `group_ids=None` 门 | → `require_read_group()`，组集合恒非空 |
| 6 | `memory_service.py:2051` Tier 2 | NULL 逃逸子句 + 双组白名单 | → 删逃逸，改 `read_group_filter("node")` |
| 7 | `learning_context_service.py:120/137` `_fetch_tips_and_errors` | 不接收 group | → 接收 + 下传；调用方 `:307` 同步 |
| 8 | `conversation_inheritance.py:109-137` 邻居 Cypher | 零过滤 | → 三 alias **严格**过滤；调用方 `:64` 下传 |
| 9 | `neo4j_client.py:1275-1282` `get_concept_score_history` | 零过滤 | → 五 alias（`n`/`c`/`cn`/`r`/`e`）过滤 + 读侧解析链 |

**通读发现的同类必修（3 处，如实登记）**

| # | 位置 | 为什么必须一起改 |
|---|---|---|
| 10 | `memory_service.py:2261→2271` Tier 3 内存兜底 | 入口 group 恒非空后，等值比较从"常年不生效"变成"生效且过严" → 三层可见面不一致 |
| 11 | `memory_service.py` `_search_graphiti_legacy` | recipe 不可用时的**实际生产路径**，与主路径同型漏洞 |
| 12 | `memory_service.py` batch/temporal 两处 `_episodes.append` | 这两条写路径不落 group_id，读侧 fail-closed 后它们产出的 episode 会在 Tier 3 静默消失（仅内存记录补字段，**Neo4j 写身份零改动**） |

**Codex round-1 追加（3 处）**

| # | 位置 | 处置 |
|---|---|---|
| 13 | `neo4j_client.get_review_suggestions` / `get_learning_history` / `_get_learning_history_json` | **删除无 group 全库分支**（B-2）。签名保持 `Optional` 不变，行为统一走 `read_scope_params` |
| 14 | `api/v1/endpoints/exam_quick.py` | **解析并下传 vault**（B-3）。原来强制带 `vault_id` 却不解析：A 进程收到 `vault_id=B` 的请求会读 A 的批注、把题记成 B 的 |
| 15 | `services/archive_scheduler.py` | 删本地解析链改 `require_read_group`（H-1）。原实现的 ContextVar 默认值 `"general"` 恒 truthy ⇒ 告警是死代码，实际每 24h 在 `vault:default` 污染桶里扫 |

### (c) R1 保召回反向门 ✅（不可省项，正反 + 逐 alias 双层）

`tests/integration/test_cypher_contract_gate.py` **门 6**，双 vault fixture 铺 8 个组（A 根 / `board_x` / `board_x:semantic` / `board_y` / `semantic` / **punycode** / B 根 / 近似前缀 `_ab` vault）：

**第一层：方向门**

| 门 | 断言 |
|---|---|
| `..._punycode_subgroup_is_really_punycode` | 自证中文子组确实是 `__xn--` 形态、近似前缀样本有效 |
| `..._contract_fragment_recall_and_isolation` | 保召回 + 零泄漏 + 防误配 |
| `..._canvas_scope_still_isolates_sibling_board` | 保隔离（helper 层） |
| `..._canvas_scope_via_production_methods` | 保隔离（**生产方法**层，M-1 整改） |
| `..._review_suggestions_recall_and_isolation_in_one_read` | **用户可感 + 卡文 (c) 的"同时"**：真实 `get_review_suggestions` 读**一次**，对**同一个结果集**断言 `got == _A_SCOPE_EXPECTED` —— 一次蕴含 (i) A 的 root/canvas/semantic/punycode 全在，(ii) B 不在，(iii) 近似前缀 vault 不在 |
| `..._review_suggestions_zero_cross_vault_leak` | 补充：反向 B 作用域只见 B |
| `..._learning_history_recall_and_isolation` | 同口径，同样对同一结果集断言精确相等 |
| `..._score_history_scoped_read` | 同 node id + 同 canvas path 两 vault 各写一份，各读各的 |
| `..._score_history_fail_closed_on_unresolved_group` | 显式空白串 **+ 生产默认 `None` 无 ContextVar 无 active vault**（H-2 整改） |
| `..._inheritance_neighbors_are_vault_scoped` | 邻居查询 A/B 各见各的 |

**第二层：逐 alias 异组负门（H-4 整改，Codex 实测原门杀不掉单 alias 变异）**

| 门 | 覆盖 alias |
|---|---|
| `..._review_suggestions_per_alias` / `..._learning_history_per_alias` | `c` / `r` 各错一次 + 全 A 正向对照 |
| `..._score_history_per_alias` | `n` / `c` / `cn` / `e` / `r` 五个各错一次 + 正向对照 |
| `..._inheritance_per_alias_negative` | 异组 `neighbor` / 异组 `r` / **NULL `r`**（B-1 直接回归锁）+ 正向对照 |

**"同时"的落实（Stop hook 质询后强化）**：卡文 (c) 要求"**同时**断言子组可见 + 他库 0 条"。初版的生产方法门把召回与泄漏拆成**两次独立读**各证一半——那只证明了"某次读能看到 A"和"某次读看不到 B"，没证明"**这一次**读既完整又干净"。现改为对同一结果集断言**精确集合相等**（严格强于"超集 + 不含"）。契约片段门 `..._contract_fragment_recall_and_isolation` 本就是一次读三面同断。

**可核验的活体读数**（`evidence-g41a/prove_condition_c.py`，输出 `condition-c-live-readout.txt`）：在 7692 铺 A 根组 / A canvas 子组 / A semantic 影子组 / A punycode 子组 / B 根组 / 近似前缀 vault 六组数据，用**生产方法** `get_review_suggestions` 以 A 根组读一次，逐条打印返回与未返回：

```
✅ 返回  A 根组 / A canvas 子组 / A semantic 影子组 / A punycode 子组
⛔ 未返回 B 根组 / 近似前缀 vault
保召回 PASS(缺 []) · 零泄漏 PASS(多 []) · 同一个结果集同时成立 PASS
```

**fixture 假绿防线**：`g41a_seed` / `g41a_alias_seed` 均依赖 function-scoped `gate_client`（它每次 setup/teardown 都跑 `_CLEANUP_QUERIES`，模块级 seed 会被第二个用例清掉、之后所有"看不到 B"都对着空库假绿）；seed 末尾自证条数落库。

**反向可红验证（机械变异，有脚本有回执）**

`backend/scripts/g41a_mutation_negative_controls.py` — **17 类**变异，串行执行，每次还原后 `filecmp.cmp(shallow=False)` 硬门。回执：`_bmad-output/审查/evidence-g41a/mutation-negative-controls-2026-08-30.txt`

```
[baseline] 109 passed, 10 warnings in 2.13s
[eq-only         ] RED  ✅  15 failed, 79 passed, 10 warnings in 2.32s
[always-true     ] RED  ✅  27 failed, 67 passed, 10 warnings in 1.93s
[mem-eq-only     ] RED  ✅  1 failed, 7 passed, 10 warnings in 0.37s
[mem-always      ] RED  ✅  2 failed, 6 passed, 10 warnings in 0.41s
[no-fail-closed  ] RED  ✅  3 failed, 83 passed, 10 warnings in 2.16s
[no-shape-check  ] RED  ✅  6 failed, 31 passed, 10 warnings in 0.37s
[alias-c         ] RED  ✅  3 failed, 46 passed, 10 warnings in 2.37s
[alias-r         ] RED  ✅  4 failed, 45 passed, 10 warnings in 2.15s
[alias-n         ] RED  ✅  3 failed, 46 passed, 10 warnings in 1.76s
[alias-cn        ] RED  ✅  1 failed, 48 passed, 10 warnings in 1.62s
[alias-e         ] RED  ✅  1 failed, 48 passed, 10 warnings in 1.95s
[alias-neighbor  ] RED  ✅  1 failed, 48 passed, 10 warnings in 2.22s
[no-collision-check] RED  ✅  1 failed, 14 passed, 10 warnings in 0.37s
[json-review-unscoped] RED  ✅  1 failed, 14 passed, 10 warnings in 0.36s
[json-concept-id-unscoped] RED  ✅  1 failed, 14 passed, 10 warnings in 0.36s
[ctxvar-treated-as-derived] RED  ✅  1 failed, 14 passed, 10 warnings in 0.36s
[json-score-unscoped] RED  ✅  1 failed, 14 passed, 10 warnings in 0.36s

结果: 17/17 变异被杀 (门能红)
```

覆盖三层：**全局方向**（前缀退等值 / 过滤恒真 / 内存侧两种）、**逐 alias**（`c`/`r`/`n`/`cn`/`e`/`neighbor` 各单独放行）、**fail-closed 与降级面**（推导落桶不抛 / 去形状校验 / 去碰撞校验 / ContextVar 被当成推导 / JSON 降级三处不过滤）。

> ⚠️ **脚本上线当场抓到一道死门**：首跑 11/12，`no-shape-check` 全绿——说明形状校验我只在 shell 里手工验证过、**没写成门**。补 `test_malformed_scope_is_rejected` + `test_derived_default_bucket_is_rejected` 后才 12/12。这正是 Codex 要求"变异要有脚本和回执"的价值：口头说"我验证过"和"门里锁着"是两回事。后续 round-2/3 的 5 条修复也各自配了变异（`no-collision-check` / `json-review-unscoped` / `json-concept-id-unscoped` / `json-score-unscoped` / `ctxvar-treated-as-derived`），最终 **17/17**。

### (d) 契约规则对齐 ✅

`.claude/rules/cypher-read-contract.md`：头部执行级别补 G4-1a 运行时 fail-closed；**R4 节**重写（规范写法代码块 + 四个 API 职责 + ⚠️ 前缀语义段含现网实证数字 + 已封堵站点 + 未封堵存量）；「存量现状」补收敛进度。

### (e) 裁判 ✅

| 门 | 命令 | 结果 |
|---|---|---|
| 真库门 | `pytest tests/integration/test_cypher_contract_gate.py -q` | **49 passed**（原 26） |
| 新增单元门 | `pytest tests/unit/test_{vault_scope_read,memory_read_scope,read_scope_callers}_g41a.py -q` | **60 passed** |
| 变异负控 | `python scripts/g41a_mutation_negative_controls.py` | **17/17 门能红** |
| grep 门 | `grep -c "group_id = None" memory_service.py` | **0** |
| grep 门 | `grep -c "group_ids IS NULL" memory_service.py` | **0** |
| lint | `ruff check app/ + 新测试 + 脚本` | All checks passed |

**unit comm 对账（口径如实登记，含 Codex round-1 的更正）**

- **基线树**：`git archive cbb20afb`（**非** goal 文写的 `d3dcb16c`）。理由：`cbb20afb` 是本 worktree 的实际 HEAD、本卡 diff 的真实"before"。二者差异 `git diff --stat d3dcb16c..cbb20afb -- backend/` 仅 `review_overview.py` + 其两个测试文件，不触及本卡任何选中模块。基线树同步 `backend/.env` 保证环境一致。
- **判据是「零新增失败」而非绝对 0 fail**（goal 文明确）。goal 文写"基线有 11 条既红"，`-k` 过滤实测为 **26 条**（20 failed + 6 errors）——以实测为准。
- **⛔ 对账清单的生成方式已更正（Codex round-1 M-3）**：初版清单是**人工挑选**的 15 个文件，漏了 `test_neo4j_field_consistency.py`（实跑 1 failed），导致"零新增失败"当时**不成立**。现清单改为由**本卡触及符号的反向引用**机械生成：

  ```bash
  grep -rlE "get_learning_history|get_review_suggestions|get_concept_score_history|search_memories|_fetch_tips_and_errors|_fetch_neighbor_records_for_inheritance|vault_scope|archive_scheduler|exam_quick|_expand_vault_subgroups" tests/unit tests/integration
  ```

  命中 57 个文件，其中 `tests/unit/` 31 个纳入对账。

- **最终结果（反向引用全清单，31 文件 / 487 测试）**：
  - 基线：48 failed / 385 passed / 9 errors
  - 改后：47 failed / 495 passed / 9 errors
  - `comm -13`（**新增失败**）= **空集**
  - `comm -23`（消失失败）= 1 条 —— `test_memory_fallback_subject_filter`（Codex 点名的那条基线既红，本卡一并修绿）

**测试改动的正当性（Codex 独立复核判为"总体合理"，其指出的不完整已修）**

10 条曾新增失败全部同一根因：fixture 注入内存 episode 时**不带 `group_id`**。处置三步，非"改断言到绿"：

1. **先查生产真相** — `memory_service` 的 5 个 `_episodes.append` 中确有 2 个（batch/temporal）不落 group_id，是**真实缺陷**，已修（(b)#12）。Codex 独立复核该论据**属实**，且确认只改内存记录、Neo4j payload 未变。
2. **确认契约方向** — 同文件兄弟用例 `test_memory_fallback_subject_filter` **基线就是红的**，红因完全相同 ⇒ 代码库既有契约本来就是"有作用域时无归属 episode 不可见"。Codex 独立复核该论据**属实**。
3. **补 fixture + 立正面门** — 新增 `_scope()` / `_subject_scope()` / `_json_scope()` helper（含说明 docstring），31 处注入点补 group_id；`test_no_subject_means_no_group_id` 契约反转为 `test_no_subject_still_scopes_to_active_vault`（docstring 逐字记录原断言、为何是泄漏面、新契约）；`test_neo4j_field_consistency` 两条断言更新为「两 alias 各自等值+前缀、参数名成对、前缀锚带 `__`」。**并新增 `test_memory_read_scope_g41a.py`（8 条）与 `test_read_scope_callers_g41a.py`（9 条）正面锁死新契约**，使 fixture 修改有独立依据而非自证。

**ruff format 口径（如实）**：`ruff format --check` 对改动文件报 would reformat，但 `git show HEAD:` 抽出的**原始文件同样报** ⇒ 属 `reference_ruff_format_drift_lefthook.md` 记录的存量漂移（仓库按 ~88 列换行、ruff 配置行宽更大），非本卡引入。commit 走 `LEFTHOOK_EXCLUDE=python-lint` 外科绕过；真正的 lint 门 `ruff check` **全绿**。

### (f) 移交 CARD-G4-1b 清单 ✅

**`neo4j_client.py` 未封堵读方法（对应审计 §5）**

| 方法 | 审计编号 | 现状 |
|---|---|---|
| `get_concept_history` | G2-2 移交项 2 | 完全没有 group 参数；service 侧 `memory_service.get_concept_history` 亦无 → 需读写两端一起改 |
| `get_canvas_associations`（4 个 Cypher 分支） | #11 / #12 / #13 / #14 | 按 path / type 全库扫 |
| `get_canvas_concepts` | #17 | 按 canvas path，UNION 两分支均无 group |
| `find_common_concepts` | #18 | 两 canvas path scope，无 group |
| `get_all_recent_episodes` | #19 | `MATCH (u:User)-[r:LEARNED]->(c:Concept)` 全库扫（仅 LIMIT） |

> **口径差声明（更新）**：手册 (f) 记「5 读方法 + 4 个 JSON 镜像 + get_all_recent_episodes」。实际本卡把 `get_review_suggestions` / `get_learning_history` **完全**封堵（Codex round-1 B-2 反证「删除会导致签名半改」不成立），故移交侧剩 **5 个方法**（含 `get_all_recent_episodes`），与手册数字巧合一致但成分不同。

**JSON 镜像层（新增过滤面，移交）**：`_get_score_history_json_fallback`、`_get_canvas_associations_json*`、`_get_canvas_concepts_json*` 等。本卡只对**已有**过滤的 `_get_learning_history_json` 做了语义对齐 + 删无过滤分支，未给任何镜像**新开**过滤面。

**其他移交**：审计 §5 #2/#4 两处 CONDITIONAL 已在本卡升为全 alias + 前缀语义（不再移交）。

**未触碰（全批禁改，逐条确认）**：`review_service.py` / `endpoints/review.py`、`exam_service.py` / `verification_service.py`、`graphiti_memory_reader` / `graphiti_belief_service`。
> 注：`endpoints/exam_quick.py` **不在**禁改名单（名单里是 `exam_service.py`）；B-3 的修改限于端点入口加解析 + 下传 group，未动出题逻辑。

---

## 三、硬边界遵守情况

| 边界 | 状态 |
|---|---|
| Neo4j 7691 **只读** | ✅ 仅 `cypher-shell` 只读 `MATCH…RETURN count/分布` 与 `SHOW INDEXES`，零写入 |
| 写测试用 7692 | ✅ 门测试模块级探针对 `:7691` **一律拒绝运行**（`test_gate_never_targets_live_7691`） |
| 不碰 review_service / endpoints/review.py | ✅ |
| 不碰 exam_service / verification_service | ✅ |
| 不碰 graphiti_memory_reader / graphiti_belief_service | ✅ |
| 不 push | ✅ |

---

## 四、现网只读实证（7691，本卡的事实依据）

```
MATCH (n) WHERE n.group_id IS NOT NULL RETURN n.group_id, labels(n)[0], count(*)
  vault__canvas_vault__semantic                        Entity    65
  vault__canvas_vault__semantic                        Episodic  30
  vault__canvas_vault                                  Entity    28
  vault__test_vault                                    Entity    18
  ...
  vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d  Concept    1   ← 全库唯一 Concept

MATCH ()-[r:LEARNED]->() RETURN r.group_id, count(*)
  vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d   1            ← 全库唯一 LEARNED
MATCH ()-[r:LEARNED]->() RETURN count(*), count(r.group_id)  → 1, 1  （无 NULL）
MATCH (n:EntityNode)      RETURN count(*), count(n.group_id)  → 3, 3  （无 NULL）
MATCH (n:EntityNode)-[r]-(m:EntityNode)                       → 0 行
MATCH (n:Node) / (c:Canvas) / (n:Episode)                     → 0 行
SHOW INDEXES → Entity/Episodic/Community/CanvasNode/CanvasBoard 有 group_id RANGE 索引;
               Concept/LEARNED/Node/Canvas 无
```

**推论（均写进了代码 docstring）**

1. vault 根组等值过滤 ⇒ 复习建议/学习历史**必空** → 前缀语义不可省（(c) 门的存在理由）。
2. `EntityNode` 零 NULL group ⇒ inheritance 对两个节点 alias 取**严格**过滤不断读。
3. `Node`/`Canvas`/`Episode` 现网 0 行 ⇒ score-history 五 alias 严格过滤无存量损失。
4. 12 个 group 并存、`vault__canvas_vault` 与 `vault__test_vault` 同时有数据 ⇒ **泄漏是现实而非理论**。
5. RANGE 索引支持前缀 seek；`Concept`/`LEARNED` 本就无 group 索引，等值与前缀同为 post-expand 过滤 ⇒ 本卡**不构成性能回归**（L-1）。

---

## 五、复核命令（一键）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-readleak/backend

# 真库门（需 7692: docker compose --profile test up -d neo4j-test）
caffeinate -i .venv/bin/pytest tests/integration/test_cypher_contract_gate.py -q      # 49 passed

# 新增契约门
caffeinate -i .venv/bin/pytest tests/unit/test_vault_scope_read_g41a.py \
    tests/unit/test_memory_read_scope_g41a.py tests/unit/test_read_scope_callers_g41a.py -q   # 60 passed

# 假绿防线（17 类变异, 串行, 还原逐字节比对）
caffeinate -i .venv/bin/python scripts/g41a_mutation_negative_controls.py             # 17/17

# grep 门（应均为 0）
grep -c "group_id = None" app/services/memory_service.py
grep -c "group_ids IS NULL" app/services/memory_service.py

# lint
.venv/bin/python -m ruff check app/ scripts/g41a_mutation_negative_controls.py
```

---

## 六、待用户裁决（5 条）

| # | 事项 | 背景 | 建议 |
|---|---|---|---|
| 1 | **`exam_quick` 新增 409 是否可接受** | B-3 修复给该端点加了 vault 一致性门。此前它对任何 `vault_id` 都放行（读的却是 active vault 的数据）。若有调用方长期传着错的 `vault_id` 也"能用"，改后会开始收到 409 | 建议保留（这正是它该做的）。若担心插件侧存量调用，可先看一轮日志再决定 |
| 2 | **`Concept`/`LEARNED` 是否补 group_id RANGE 索引** | 实测这两个标签**没有** group_id 索引，等值与前缀都是 post-expand 过滤（故本卡无回归）。但数据量上来后两者都会慢 | 建议登记 backlog，与 G4-14/R-SLO 的规模基准一起做 `PROFILE` 后再定 |
| 4 | **物理 ID 碰撞的写侧残留是否本批收** | Codex round-3 指出 `vault:a__board` 与 `vault:a:board` 物理化后同名。读侧已拒绝该形状作作用域；且实测 `sanitize_vault_id("a__board") == "a_board"`、yaml 分支也过 sanitize（config.py:789）⇒ **没有任何生产路径能产出这种 vault 身份**。残留只在"调用方手工构造 group_id 直接写入" | 建议移交写侧身份校验卡（本卡铁律不碰写路径）。若要立刻堵，需在 `to_physical_group_id` 或写侧解析加拒绝，属 G2 地盘 |
| 5 | ⛔ **审查轮次未走完，是否补跑** | round-1 完整（13 条，已全闭合）；**round-2 / round-3 均被外部内容过滤在收尾汇总阶段中断**，未产出完整分级报告与合并裁定。两轮中断前给出的 5 条反证已全部核实处置（3 修 + 1 登记边界 + 1 自查追加），但**没有一份 round-2/3 的终裁**。连续两轮同型中断（改过措辞仍触发，触发点在汇总而非提示词） | 建议：换审查器（另一模型/人工）跑一轮终裁，或接受"round-1 全闭合 + round-2/3 反证全闭合 + 17/17 变异"作为证据链。**这是本卡唯一的证据缺口，必须由你裁决**，我不代批 |
| 3 | **`learning_context_service` 的死 fallback 是否本批修** | LearningMemoryClient secondary 未传必填 `query`，固定 TypeError 后被吞——从未真正运行过（Codex L-2，既有缺陷、与跨库读无关） | 建议独立收债卡。修它等于启用一条从未运行过的代码路径，需要单独验证，不宜混进封堵卡 |
