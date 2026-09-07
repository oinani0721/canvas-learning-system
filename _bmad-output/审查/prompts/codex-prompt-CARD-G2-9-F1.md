你是独立代码审查者。请对下面这次改动做对抗性审查。仓库根目录：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance
（只读；不要连任何数据库，不要执行测试。）

## 一 背景 + 最小读取面（请只读这些，不要全仓扫描）

**缺陷**：`backend/lib/agentic_rag/clients/lancedb_client.py` 的 `_cache_tables()`
把 `db.table_names()` 的**全部**表（含**别的 vault 前缀**的表）送进
`_check_and_fix_dimension_mismatch()`，后者对「向量维度不符」或「缺 doc_type 列」
的表直接 `drop_table`。于是 vault A 的 `initialize()` 会删掉 vault B 的表——
一个 vault 的进程能删掉另一个 vault 的数据。该现象由 canary 端到端实测确认。

**本次改动**（三个文件）：
1. `backend/lib/agentic_rag/clients/lancedb_client.py`
   - 新增模块级哨兵 `_UNSET` 与方法 `_owns_table(name, vault_id=_UNSET)`（归属规则单点）
   - `_cache_tables` 的维度检查列表加 `_owns_table(t, self.active_vault_id)` 过滤
   - `_cache_tables` 与 `list_vault_tables` 的表名来源改用既有的 `_all_table_names()`
     （绕开 `table_names()` 的 `limit=10` 默认分页）
   - `_check_and_fix_dimension_mismatch` 的存在性判断也改用 `_all_table_names()`
     （**这一处是对原任务卡的偏离，见 §二.A**）
   - `list_vault_tables` 改为透传 `vault_id` 给 `_owns_table`
2. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`（新文件，四条行为门）
3. `backend/scripts/g29_dual_vault_canary.py`（探针结果加 `verdict` 键 + `_amain` 据此返回
   `EXIT_ISOLATION_FAILED` + docstring 更正）

**最小读取面**（请按此顺序读，不要超出）：
- `git diff da690bf8 __AUDIT_SHA__ -- . ':(exclude)_bmad-output'`
- `backend/lib/agentic_rag/clients/lancedb_client.py` 的 `:762-900`、`:918-935`、
  `:1000-1060`、`:3681-3760`（改后实测范围；`_owns_table` / `list_vault_tables` /
  `_all_table_names` / `_is_table_absent` / `drop_vault_tables` / `_cache_tables` /
  `_check_and_fix_dimension_mismatch`）
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文
- `backend/tests/unit/test_archive_legacy_lance_tables_g24.py:583-630`（既有真库先例）
- `backend/tests/regression/test_rag_stage1_index_contracts.py:213-222` 与 `:484-490`
  （两条既有承重门：源码门字面量 + `list_vault_tables(None)` 的裸表口径）
- `_bmad-output/审查/evidence-g29/canary-report-20260906T021427Z.json:213-222`（缺陷实测记录）

## 二 作者自述 —— 请独立核对，不要采信

作者声称：

1. `_owns_table` 与原 `list_vault_tables:845` 的裸表口径**逐字同语义**
   （`"_" not in name or name == FINGERPRINT_TABLE`）。
2. `_owns_table` 的 `vault_id` 是三态：不传（`_UNSET`）= 用 `active_vault_id`；
   显式传 `None`/`""`/`"default"` = 裸表口径；显式传具体 vault = 该 vault 前缀。
   显式 `None` 的裸表口径是既有承重契约（`test_rag_stage1_index_contracts.py:489-490`）。
3. 四条门各自带前提断言（夹具真的建成了预期形态才让主断言说话）。
4. 三段负控各拆一层防线，每段都红在声称的那条断言上，且源文件 sha 前后逐字相同。
5. `_tables_cache` 的**装载循环**未改；但装载**集合**因分页收口从「前 10 张」扩到「全库」，
   这会改变 `:938`（initialize 日志）与 `:3950`（get_stats 的 "tables"）两个读者的输出。
   实测：12 表夹具下改前长度 10、改后 12。

### §二.A 四处对原任务卡的偏离（请重点核对是否正当）

- **A1** 原卡要求 `_check_and_fix_dimension_mismatch` 的存在性判断（原 `:3650`）**不动**。
  作者改了它。作者给的理由与实测证据：不改则该行的 `self._db.table_names()` 仍是
  `limit=10` 默认分页，第 11 张之后的表被判为「不存在」直接 `return False`，于是
  `_cache_tables` 那边的分页收口对启动自愈**完全无效**（扫描面扩大了，每张越界表却在
  这里被挡回去）。实测：`_tables_cache` 已含 `a_t11`、`_owns_table('a_t11')` 为 True，
  但直接调 `_check_and_fix_dimension_mismatch('a_t11', 8)` 返回 False 且表仍在。
  请核对：这个改动是否安全？它的另一个调用方（`add_documents` 路径，改后 `:3822` 附近）
  会不会因「原本误判为不存在的表现在判为存在」而行为改变？
- **A2** 原卡的门②/门④ 举例断言「裸表 `canvas_nodes` 归 default」。作者实测
  `list_vault_tables:845` 的判据是「表名**不含任何下划线**」，所以 `canvas_nodes`
  （含下划线）**不归** default。作者按实测口径改写了门的表名（加了无下划线的 `notes`
  覆盖「归 default」分支）。请核对：作者对 `:845` 的读法对不对？门有没有因此被放宽？
- **A3** 原卡的静态判据「AST 口径 `report.get` 调用数收工 ≥ 1」在**开工就已经是 1**
  （脚本别处已有一个 `report.get`），是一条恒真的死判据。作者把它收紧为「收工 ≥ 2」。
  请核对：真正承重的判据是哪一条？
- **A4** 原卡说 canary「只改两处」。作者改了三处——第三处是
  `probe_schema_drift_side_effect` 的 docstring（原文写「返回观察结果（不做判据）」，
  加了 `verdict` 之后这句话变成假的）。请核对这处更正是否恰当、有无夹带其它改动。

## 三 请按重要性排序回答这些问题

0. `_owns_table` 的哨兵默认值是否**真的**区分了「未传参」与「显式传 `None`」？
   在一个 `vault_id` 非空的 client 上，`list_vault_tables(None)` 是否仍是**裸表口径**？
   本卡门④ 与既有门 `test_rag_stage1_index_contracts.py:489-490` 的口径有没有偏差？
1. default（空前缀 / `"default"`）分支有没有退化成「全表都归它」或「一张都不归它」的路径？
2. `_all_table_names()` 替换后，`drop_vault_tables` 的语义变化（原先只删得到前 10 张）
   是否有调用方依赖旧行为？`_all_table_names()` 自身在 lancedb 0.30.2 上的两条分支
   （`list_tables(limit=None)` / `table_names(limit=10_000)`）是否都安全？
3. 门③ 的 12 张表夹具是否**真的**越过了分页边界？判据读回表名时有没有也走默认分页
   （那样门就只能看见前 10 张 = 给自己蒙眼）？
4. 门① 的正向对照（`a_canvas_nodes` 被 drop）是否**证明了**「本 vault 仍自愈」，
   还是它可能被别的原因删掉？
5. 源码门要求 `_cache_tables` 的源码里保留 `endswith` 与 `FINGERPRINT_TABLE` 两个字面量。
   作者保留了。这种「保留字面量」的门会不会掩盖了语义变化？
6. 四条门里有没有哪一条，即使缺陷仍然存在也会变绿（即：不承重）？

## 四 输出格式

逐条给出：`[BLOCKER|HIGH|MEDIUM|LOW]` + `file:line` + 一句话说明「在什么条件下会出问题」。
没有问题的维度请明确写「未发现问题」，不要省略。最后给一句总体判断。

## 五 边界

- 只读审查。不要修改任何文件，不要执行测试，不要连接任何数据库或网络服务。
- 不评 `_check_and_fix_dimension_mismatch` 的 **drop 条件设计本身**
  （「维度不符 / 缺 doc_type 就删」是既有裁定，不在本次改动范围）。
- 不评完整 canary 的端到端运行（本次未跑，需要额外的模型与容器依赖）。
- 不评 `list_vault_tables:845` 的裸表口径**本身**是否合理（那是 RAG-S1 H3 的既有裁定）；
  只评本次改动有没有把它改坏。
