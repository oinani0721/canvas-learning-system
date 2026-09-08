# CARD-RED-C2（U11-B）进度存档

> 车道 `card-u11-red-c` · 分支 `card/u11-red-c` · 开工 HEAD `5139428d`（= U11-A 末 commit）
> 更新时刻 2026-09-08 08:2x · **工作树有未提交改动**（本卡按 (m) 要求全部裁判通过后再单独 commit）

## 已完成：24 / 66

| 锚 | 条数 | 文件 | 处置 | 验证 |
|---|---|---|---|---|
| ① 安全校验器 | 9 | `test_config_neo4j.py` | 显式声明本地开发前提 `_LOCAL_DEV_ENV = {"DEBUG": "true"}` + **新增反向锚 3 条** | 12 passed |
| ② 权重方向翻转 | 9 | `test_supplementary_reranker.py` | 2 条改期望值（抄写字面量非 import 常量）；7 条重造数据 `note`→`image_ocr` 使 floor 仍触发 | 56 passed |
| ③ 归档路径 | 5 | `test_story_30_24_boundary.py` | `xfail(strict=True)` 交接 `CARD-VAULT-FRESHNESS-COVERAGE` | 5 xfailed |
| ④ 安全面 | 1 | `test_story_30_24_boundary.py` | 改参数名/值形态断言 + **加固**（任何 kwarg 值不得入 query 文本） | passed |

三文件集合验证：`99 passed, 5 xfailed`，`FAILED` 无，`grep -c XPASS` = 0，rc=0
（存档 `files-anchors-<ts>.txt`）。

## 依据 sha（已实测，逐条待写进 c2-verdicts.md）

| 锚 | 依据 sha | 实测命令 |
|---|---|---|
| ① | `f718d040` 2026-05-08 | `git log -S'validate_security_defaults' -- backend/app/config.py` |
| ② | `fcd34953` 2026-08-09 | `git log -S'"note": 1.0' -- backend/app/services/supplementary_reranker.py` |
| ③ | `146218b5` 2026-03-24 | `--diff-filter=D` 旧路径 与 `--diff-filter=A` `_archive/` 同一 commit ⇒ 归档非删除 |
| ④ | `4db8e94a` 2026-08-30 / `88cb13a7` 2026-08-31 | `git log -S'read_scope_params' -- backend/app/clients/neo4j_client.py` |

## 关键探针证据（已落盘）

- `anchor4-security-probe.txt` — 恶意串物理化为 `'vault__script_drop_table_users'`（**被净化**非仅改名）；以 `$group_id`/`$group_prefix` 命名参数传入；原始串与 `DROP`+`TABLE` 均不在 query 文本；无 kwarg 值被拼进查询 ⇒ **卡文 (f) 的停机条件不触发**，属演进非回归。
- `anchor2-floor-probe.txt` — floor 机制**仍在生效**：`image_ocr`(0.5×0.6=0.30<0.42) 触发 floor、`min_keep=0` 正常关闭、kill_ratio 分支正常；原 `note` 数据（现 1.0 ⇒ 0.50>0.42）不再落在误杀区间，这正是 9 条红的机制。

## 剩余 42 条 / 20 文件

`test_agent_service_comparison` 6 · `test_rag_multimodal_integration` 4 · `test_cache_configuration` 4 ·
`test_agent_service_neo4j_memory` 4 · `test_agent_context_injection` 4 · `test_story_38_4_dual_write_default` 3 ·
`test_story_38_1_review_fixes` 2 · `test_context_enrichment_2hop` 2 · `grouping/test_analyze_canvas` 2 ·
其余 11 文件各 1（`test_wave5_stageb_continued_vault_id_injection` / `test_verification_service_injection` /
`test_subject_isolation` / `test_story_38_8_fallback_sync` / `test_story_1_7_env_config` / `test_s02_search_upgrade` /
`test_s02_entity_types` / `test_neo4j_health` / `test_intelligent_parallel_endpoints` /
`test_degraded_flag_propagation` / `test_agent_memory_trigger`）

已见的失败身份分型（`identity-open-20260908T080533.txt`）：
`ContextEnrichmentService` 缺 `_search_graphiti_relations` / `__init__` 多余 kwarg（4+2+2）·
`app.main` 缺 `set_session_validator`（3）· `500 == 404`（3，其中 3 条属 R 族不归本卡）·
`_fuse_rrf_multi_source` ImportError（2）· group_id 格式 `vault:default:物理` vs `物理:力学`（2）· 其余零散。

## 未完成的卡文条目

- (b) 66 行依据表 `c2-verdicts.md` —— 尚未创建（24 条的素材已在本文件与探针存档里）
- (g) 其余 42 条
- (h) vault fixture 硬约束核对（`autouse=True` 开工/收工对比）
- (i)(j)(k) 全量裁判
- (l) Codex 多轮
- (m) 单独 commit
- (n) 「本卡未证明什么」+「台账待登记条目」

## 本卡已发现、待写进验收单的事实

1. 同文件 `test_min_keep_floor_excludes_quarantine_taint`（`:767/:773`）与 `test_floor_not_triggered_when_enough_pass` **不在** 66 条内、当前绿 ⇒ 锚② 的数据替换按 AST 函数边界圈定，**未**全局替换 `"source_type": "note"`（全局替换会碰到 `:625/:767/:773` 三处，可能产生 `>` 行）。补丁脚本带前置断言（区间内 9 / 区间外 3）与后置逐行验证。
2. (j) 判据的**来源② 为空集** —— U11-A 的 2 条移交在 `test_qa_38_6_scoring_reliability_extra.py`，不在本卡 23 文件内；且落在本卡文件里的 4 条 C1 开工时已全绿 ⇒ 卡文的「U11-A 未完成」停机条件不触发。
3. 卡文两处坑均实测复现：`sed -n '133,198p'` 只取到 65 条且漏掉参数化那条；参数化 nodeid `grep -c` = 0 而 `grep -cF` = 1。

## 判据的采样性质（2026-09-08 自我降级，勿写强）

本卡文件级裁判耗时在 **0.41–0.78s** 量级。三次跨车道 `/tmp` 负控窗口期间，
文件级轮次全部干净（污染计数 0 / ERROR 0），但**这不是因为有任何保护，而是
窗口窄到撞不上**——同一份代码的目录级轮次（约 4 分钟）在同期三轮里被撞了两轮。

⇒ 准确表述：**「未被撞上」≠「不会被撞上」**。前者是采样结果，后者需要
「窗口宽度 × 干扰频率」的论证，本卡没有。验收单里只写前者。

附（U10-A 提供、本卡采纳的精度修正）：卫生门的 before/after 快照发生在
session fixture 进入/teardown 时，**不是进程起止时点**，两者差一个收集期。
该近似对分钟量级轮次无害，对亚秒级轮次会翻转结论。

## 剩余 42 条的根因归族（2026-09-08 分析完成，实现待续）

失败身份已 100% 解析（`c2-identities.md`，66/66，rc=0）。按根因归族如下，
**每族的依据 sha 已实测**，可直接进 (b) 表：

### 族 A — ContextEnrichmentService 改名（4 条）→ 处置：改断言指向新名
依据 **`5d2b95ba`** 2026-03-29 `refactor(S34): G-FAKE-001 — 批量重命名假"graphiti"标识符为真实Neo4j名称`
实证（`git show 5d2b95ba -- context_enrichment_service.py`）：
`-    async def _search_graphiti_relations(` → `+    async def _search_learning_relations(`；
构造参数 `graphiti_service` → `learning_memory_service`。**纯改名，能力仍在**
（现行 `context_enrichment_service.py:1011 async def _search_learning_relations`）。
⇒ `test_agent_context_injection.py` 4 条断言指向旧名，改指新名即可，不需交接。
⚠️ 注意 `class ContextEnrichmentService` 在 **`context_enrichment_service.py`**，
不在 `context_enrichment.py`（后者不存在——本卡一度按后者 grep 得到全空，
是「搜索面划窄=假阴性」，已当场纠正）。

### 族 B — association cache 整体裁撤（4 条）→ 处置待定（倾向 xfail 交接）
依据 **`836d0986`** 2026-03-31 `feat(Epic2): architectural pruning — remove cross_canvas + textbook + fix vault_notes`
实证：该 commit 对该文件 **148 insertions / 700 deletions**，删除行含
`-        association_cache_maxsize: int = 1000,  # Story 36.13 AC-5`、
`-        self._association_cache: TTLCache = TTLCache(...)`、`-        self._association_cache_lock`、
`-        cached_result = self._association_cache.get(canvas_path)`、`-            "association_cache_hit",`。
现行 `__init__` 只剩 `(self, canvas_service, learning_memory_service=None)`。
⇒ 能力**已被有意裁撤**，不是改名。`test_cache_configuration.py` 4 条
（`test_cache_default_maxsize` / `test_cache_uses_custom_maxsize` /
`test_enrichment_extreme_maxsize_1` / `test_enrichment_service_di_passes_cache_config`）
的被测对象不存在 ⇒ 按卡文 (g)「禁为凑绿降级断言」，应走 xfail(strict=True) 交接。
**待查**：`ENRICHMENT_CACHE_MAXSIZE` 是否与 C1 的 `MEMORY_RETRY_*` 同形（配置项仍在、
零消费方）——若是，交接卡可并入 `CARD-CONFIG-CLEANUP`。

### 族 C — enrich_with_adjacent_nodes 签名变更（2 条）→ 依据待取
现行签名 `(self, canvas_name, node_id, hop_depth=1, include_learning_memory=True)`。
`test_context_enrichment_2hop.py` 2 条传了已不存在的 kwarg（身份：
`TypeError: ... got an unexpected keyword argument`）。**待做**：取具体 kwarg 名 + `git log -S`。

### 族 D — 其余（32 条，各族依据待取）
- `test_agent_service_comparison` 6：`mock_call_agent() got an unexpected keyword argument 'canvas_name'`（测试自身 mock 签名与生产调用不符）
- `test_agent_service_neo4j_memory` 4：Cypher 从 `MATCH (m:LearningMemory)` 改为 `(m:EntityNode)`；格式化输出去掉了分数
- `test_rag_multimodal_integration` 4：`_fuse_rrf_multi_source` / `_fuse_weighted_multi_source` 从 `agentic_rag.nodes` 消失（⚠️ 该包是 re-export 包，见记忆 `reference_agentic_rag_nodes_ghost_package`，真身在 `_nodes_impl`）+ 1 条 coroutine 未 await
- `test_story_38_4_dual_write_default` 3：`app.main` 缺 `set_session_validator`（与 U11-A 的 (e) 同文件不同符号）
- `grouping/test_analyze_canvas` 2：group_id 格式 `vault:default:数学` vs `数学:离散数学`（D16 格式演进）
- `test_story_38_1_review_fixes` 2：`'MagicMock' object can't be awaited`
- 其余 11 文件各 1：`15 == 14`（agent 数）/ `409 == 200` / 超时文案 `30000ms` vs `500ms` /
  `'math-group__semantic' == 'math-group'` / recipe 集合多项 / 硬编码路径 /
  `Neo4j connection lost` / `'str' object has no attribute 'value'` /
  `get_graphiti_temporal_client` 未被调用 / `resolve_vault_group_id` 未从共享模块导入 / `0.0 < 0.0`
