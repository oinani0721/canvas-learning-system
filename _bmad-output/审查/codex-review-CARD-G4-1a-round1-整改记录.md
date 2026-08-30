# CARD-G4-1a Codex round-1 整改记录

> **审查存档**: `codex-review-CARD-G4-1a.md`（gpt-5.6-sol / ultra / read-only，含子 agent 交叉核查与 Python 探针实证）
> **round-1 裁定**: 需整改，不可合并（FAIL）— 3 BLOCKER + 4 HIGH + 4 MEDIUM + 2 LOW
> **整改日期**: 2026-08-30
> **批次**: BATCH-2026-08-29-第六批 / 车道 T1

Codex 的每一条都核实为**属实**，包括它对我验收单里两处表述的反证。下表逐条记处置。

## 处置总表

| # | 级别 | 问题 | 处置 | 证据 |
|---|------|------|------|------|
| B-1 | BLOCKER | inheritance 邻居查询对关系 alias `r` 用 `allow_null=True`，违反 R1「每个 alias 逐一过滤」。我原来的理由「两端节点已锚定 ⇒ 边不可能跨库」在 W1 clobber 存量图上**不可证**：两节点可现归 A，而一条曾在 B 上下文生成的边仍是 NULL group、其 `label`/`reason` 承载 B 的语义——而本查询恰恰返回这两个字段 | **已修** — 三 alias 一律严格（去 `allow_null`）；docstring 逐字记录原理由为何不成立 | `test_g41a_inheritance_per_alias_negative`（NULL 边 / 异组边 / 异组邻居三种都必须不可见 + 全 A 正向对照） |
| B-2 | BLOCKER | client 的无 group 全库分支仍在（`get_review_suggestions` else、`get_learning_history` 的 `if group_id:`）。我原称「删除必然导致签名半改」——Codex 反证**不属实**：可保留 `Optional` 签名、方法入口统一 `read_scope_params`、只删无过滤分支 | **已修（采纳其修法）** — 两个方法的无过滤分支删除，签名不变；JSON 镜像 `_get_learning_history_json` 同修（降级路径不该变成"整个 JSON 库全返回"） | `test_client_review_suggestions_has_no_unscoped_branch`、`test_read_without_group_id_still_scoped` |
| B-3 | BLOCKER | `/api/v1/exam/quick` 强制带 `vault_id` 却完全不解析不下传：进程 active=A、请求 `vault_id=B` 时读 **A** 的批注，再把题目记成 B 的（canvas node id 非全局唯一，A/B 同名节点直接串库） | **已修** — endpoint 在 try 外走 G2-2 统一解析点 `resolve_vault_group_id`（不一致即 409），解析结果显式下传 `_fetch_tips_and_errors`；frontmatter 路径因 409 门在先，只可能是同一 vault | `test_exam_quick_forwards_resolved_scope`、`test_exam_quick_rejects_other_vault`（含"409 必须发生在任何读取之前"） |
| H-1 | HIGH | 「不回落 DEFAULT_GROUP_ID」不成立：`sanitize_vault_id("")` 返回 `"default"`，配置坏掉的进程稳定推导出 `vault:default` 污染桶；且 `archive_scheduler` 的 ContextVar 默认值 `"general"` 恒 truthy ⇒ 其"回落 WARNING"是死代码，实际每 24h 在污染桶里扫 | **已修** — 新增 `_validate_scope_shape`：**推导**出 `vault:default` 即 fail-closed（显式传入的 deprecated 值仍放行 + 告警，不推翻 G2-2 契约 4）；`archive_scheduler` 删本地解析链改用 `require_read_group`；测试改为先实证 `sanitize_vault_id("") == "default"` 再用其真实产物，不再绕开 sanitizer | `test_derived_default_bucket_is_rejected`、`test_fail_closed_when_no_scope_resolvable`、`test_archive_scheduler_uses_read_scope_not_default_bucket`、`test_archive_scheduler_surfaces_unresolved_scope` |
| H-2 | HIGH | `get_concept_score_history` 复用**写侧** resolver，无 ContextVar 时由 canvas 推导出 `vault__default__<canvas>` ⇒ 后台/CLI 查询成功但零命中，被上层记成正常 `empty` 并进 30s 缓存 = 静默断读 | **已修** — 改用读侧 `read_scope_params`；canvas_name 只作查询条件，不参与 vault 推导 | 门测试 `test_g41a_score_history_fail_closed_on_unresolved_group` 扩为两形态：显式空白串 + **生产默认 `None` 且无 ContextVar 无 active vault** |
| H-3 | HIGH | `VaultScopeUnresolved(RuntimeError)` 恰好落进 `conversation_inheritance` / `learning_context_service` 的 `except (RuntimeError, ConnectionError, asyncio.TimeoutError)` 降级捕获 ⇒ 配置故障被呈现成"没有邻居 / 没有 tips"；`exam_quick` 还有第二层 `except Exception → tips=[]` | **已修** — 基类改为裸 `Exception`（docstring 写明为何**故意不**继承 RuntimeError）；三处宽捕获前加显式 `except VaultScopeUnresolved: raise`；作用域解析移到降级 try **之外** | `test_scope_exception_is_not_a_runtime_error`、`test_inheritance_neighbors_raise_not_swallow`、`test_tips_and_errors_raise_not_swallow`、`test_exam_quick_scope_failure_is_not_downgraded_to_empty_tips` |
| H-4 | HIGH | 门 6 的 fixture 把一条记录的**所有 alias 放同一 group**，任一 alias 过滤丢失都被其他 alias 兜住。Codex 实测：把 `read_group_filter(alias="r")` 单独改恒真，门 6 仍 9/9 passed = 该门证明不了 R1 | **已修** — 新增逐 alias 异组负门：review/history 的 `c`/`r` 各错一次；score-history 的 `n`/`c`/`cn`/`e`/`r` 五个各错一次；inheritance 的 `neighbor`/`r`/NULL 三种。每组都配**全 A 正向对照**（防"写死成空"假绿） | `test_g41a_review_suggestions_per_alias`、`test_g41a_learning_history_per_alias`、`test_g41a_score_history_per_alias`、`test_g41a_inheritance_per_alias_negative`；变异脚本 `alias-*` 六类逐个杀门 |
| M-1 | MEDIUM | canvas 子组隔离只测 helper，没经过生产方法 ⇒ 生产方法若把 `vault:A:board_x` 错误提升成 `vault:A`，helper 门与根组生产门都仍绿 | **已修** — 新增 `test_g41a_canvas_scope_via_production_methods`：用 `get_review_suggestions` / `get_learning_history` 传 canvas 作用域，断言只见 board_x 及其 semantic | 同左 |
| M-2 | MEDIUM | `_expand_vault_subgroups` 是 `RETURN DISTINCT … LIMIT 50` 的**无序截断** ⇒ 超过 50 个子组时 Graphiti 侧"全部子组可见"与 Cypher/内存侧前缀语义不等价，根组搜索随机漏召回 | **已修** — 改确定性 `ORDER BY gid` + 分页取全量（page 500 / 硬上限 5000）；真撞上限则如实记入 `fail_sink` → degraded，不静默按收窄面检索 | `memory_service._SUBGROUP_PAGE_SIZE` / `_SUBGROUP_HARD_CAP` |
| M-3 | MEDIUM | 验收单「零新增失败」**不成立**：`test_neo4j_field_consistency.py` 仍断言旧 `$groupId`（实跑 1 failed）；且 `test_memory_fallback_subject_filter` 的 fixture 两条都填 vault 根组，subject 子组作用域读不到父组，定向执行仍红 | **已修 + 验收单已改口径** — field-consistency 两条断言更新为「两 alias 各自等值+前缀、参数名成对、前缀锚带 `__`」；subject fixture 改为分别落各自学科子组（新增 `_subject_scope()` helper）。**该文件此前不在我的对账清单里** ⇒ 已扩清单并重跑；验收单 §二(e) 改为登记实测口径 | 见验收单 §二(e) 修订版 |
| M-4 | MEDIUM | 显式畸形 group 被当成有效作用域：`canonical_group_id("vault:")` 原样返回 ⇒ `read_scope_params("vault:")` 得 `group_id='vault__'`，不会全库扫描但把非法配置伪装成正常空结果 | **已修** — `_validate_scope_shape` 做段级校验：非 `vault:` 前缀 / 任一空段 / 裸前缀一律抛 | `test_malformed_scope_is_rejected`（`vault:` / `vault__` / `vault:a:` / `vault: `） |
| L-1 | LOW | `STARTS WITH` 无实测规模回归；相关 group 属性缺适用索引 | **如实登记，不改** — 7691 只读 `SHOW INDEXES` 实查: `Entity`/`Episodic`/`Community`/`CanvasNode`/`CanvasBoard` 等**有** group_id RANGE 索引（RANGE 索引支持前缀 seek），但 `Concept`/`LEARNED`/`Node`/`Canvas` 没有。旧等值过滤同样是 post-expand，**本卡不构成回归**；生产规模 `PROFILE` 与索引补建登记 backlog | 验收单 §六 裁决点 2 |
| L-2 | LOW | `learning_context_service` 的 LearningMemoryClient secondary 未传必填 `query` ⇒ 固定 TypeError 再被吞，是死 fallback | **如实登记，不改** — 属既有缺陷（非本卡引入、与跨库读无关）；修它会启用一条从未运行过的代码路径，需独立验证 | 验收单 §六 裁决点 3 |

## 我方原表述的更正（Codex 反证属实，逐条认）

1. **「删除 client 无 group 分支必然导致签名半改」= 不属实**。保留 `Optional` 签名 + 入口统一解析 + 删无过滤分支，三者可同时成立。已按 Codex 修法执行。
2. **「零新增失败」= 不成立**。我的对账清单是**挑选**的文件集，漏了 `test_neo4j_field_consistency.py`（实跑 1 failed）。教训：对账清单必须由「本卡触及符号的反向引用」生成，不能靠人工列举。现清单已含该文件。
3. **变异计数「13 failed / 14 failed」= 不可验证**。当时是一次性手敲命令、无脚本无日志。已补 `backend/scripts/g41a_mutation_negative_controls.py`（12 类变异，含逐 alias），任何人可一条命令复跑，输出即回执。
4. **「逐字节恢复」当时无回执**。脚本现在把 `filecmp.cmp(shallow=False)` 做成硬门，不一致即 exit 3。

## 变异脚本自身抓到的问题（脚本上线即见效）

首跑 **11/12**，一道**死门**：`no-shape-check`（把形状校验整段跳过，门全绿）。说明我当时只在 shell 里手工验证过 `vault:` / `vault__` 被拒，**没有写成测试**。已补 `test_malformed_scope_is_rejected` + `test_derived_default_bucket_is_rejected`，复跑 12/12。

这正是 Codex 要求"变异要有脚本和回执"的价值所在：口头说"我验证过"和"门里锁着"是两回事。

## Codex round-2 追加处置（2026-08-30）

round-2 在收尾前被 cyber 过滤中断（记忆项 `reference_codex_exec_gotchas.md` 记过此坑），
但中断前已给出两条**硬反证**，均核实为真并已修：

| # | 级别 | 问题 | 处置 | 证据 |
|---|------|------|------|------|
| R2-1 | BLOCKER | **JSON 降级模式是封堵的旁路**。`_handle_query_reviews`（`get_review_suggestions` 在降级模式下的实际执行者）完全忽略 group 参数；`_get_score_history_json_fallback` 零过滤。⇒ **把 Neo4j 弄挂就能拿到全部 vault 的复习建议与分数 = 等于没封** | **已修** — 两处按同一 scope 语义过滤；review 侧缺 scope 即 fail-closed（它的 Cypher 路径已封，两侧口径必须一致）。⚠️ `_handle_query_history` 只做"有 scope 则过滤 + 无 scope 告警"：它的主调用方 `get_concept_history` 的 **Cypher 路径本卡没封**（整族移交 G4-1b），单方面在降级侧 fail-closed 会打断一个本卡不拥有的功能，而泄漏面并不因此变小 | `test_json_fallback_review_suggestions_is_scoped`、`test_json_fallback_score_history_is_scoped`；变异 `json-review-unscoped` / `json-score-unscoped` |
| R2-2 | HIGH | **物理 ID 碰撞**：`vault:a__board` 与 `vault:a:board` 物理化后同为 `vault__a__board`（`group_id_compat` 自己也对这种输入告警"roundtrip lossy"）。作为**读作用域**，一个真叫 `a__board` 的 vault 会与 vault `a` 的 `board` 子组共用可见面 —— 前缀语义在这里跨 vault | **已修** — `_validate_scope_shape` 拒绝段内含 `__` 的逻辑作用域（标准 sanitize 链会折叠连续下划线，产不出这种值；出现即配置有误） | `test_segment_with_double_underscore_is_rejected`；变异 `no-collision-check` |

**自查追加（非 Codex 提出）**：`vault:default` 的拒绝策略原本会误伤"vault 真的叫 default"的合法配置。已加 `_default_is_configured()` 判据——**必须是配置里写着 default**（`sanitize_vault_id(ACTIVE_VAULT) == "default"` 且 ACTIVE_VAULT 非空），而不是"配置里写了点什么"，否则 `ACTIVE_VAULT=canvas-vault` 的正常进程在推导异常落桶时会被误判成合法、H-1 就白做了。正反两条门：`test_derived_default_bucket_is_rejected` / `test_vault_literally_named_default_is_allowed`。

变异负控随之扩到 **15 类**（新增 `no-collision-check` / `json-review-unscoped` / `json-score-unscoped`，脚本改造为支持多目标文件），复跑 **15/15 门能红**。

## Codex round-3 追加处置（2026-08-30）

round-3 **同样**在子 agent 汇总阶段被 cyber 过滤中断（连续两轮同型；已按 `reference_codex_exec_gotchas.md` 改过措辞仍触发，触发点在**汇总**而非提示词）。中断前它给出三条静态反证，逐条核实：

| # | 级别 | 问题 | 核实 | 处置 |
|---|------|------|------|------|
| R3-1 | HIGH | JSON 复习建议**虽已过滤关系**，但 `concept_id` 是按 **name 全库反查** `self._data["concepts"]` 得到的 ⇒ 两 vault 有同名概念时会取到他 vault 那条的 id（标识符级串读） | **属实**。且 JSON `concepts` 记录确实带 `group_id`（G2-3 已加），所以可以过滤 | **已修** — 反查加 scope 条件，命中不到用关系自带 id 兜底。门 `test_json_fallback_review_concept_id_is_scoped`（他 vault 同名概念**排在前面**，全库匹配会先撞上它）；变异 `json-concept-id-unscoped` |
| R3-2 | HIGH | `vault:a__board` 的数据仍可被合法 `vault:a:board` 作用域读到——拒绝该形状作**读作用域**并不能让已落库的数据"解碰撞" | **部分属实，但生产不可达**。实测 `sanitize_vault_id("a__board") == "a_board"`、`sanitize_subject_name("a__board") == "a_board"`，且 `Settings.vault_id` 的 yaml 分支也过 `sanitize_vault_id`（config.py:789）⇒ **没有任何生产路径能产出段内含 `__` 的 vault 身份**。剩余暴露只在"调用方手工构造 group_id 直接写入"，属**写侧身份校验**，本卡不碰写路径 | **如实登记为已知边界 + 移交**（见验收单 §六裁决点 4）。读侧该形状已拒绝（`no-collision-check` 变异可杀） |
| R3-3 | **BLOCKER** | `vault:default` 的"显式/推导"判定**会被上游预解析丢失来源**：`resolve_vault_scope(legacy_group_id='cs188')` 把归一化产物 `vault:default` 注入 ContextVar，service 层再读时被当成"配置断裂推导出污染桶"而抛错 ⇒ **整条 deprecated 兼容层在读侧断掉**（G2-2 契约 4 明确本卡不推翻兼容层） | **属实，且是我 H-1 整改引入的回归**。实测 `ContextVar='vault:default'` → `require_read_group()` 抛错 | **已修** — `require_read_group` 不再调用不透明的 `current_group_id()`，改为**内联两支并分辨来源**：ContextVar 有真实值 = 有人显式设过 ⇒ `explicit=True`；只有落到 active vault 推导那一支才是 `derived`。门 `test_contextvar_injected_deprecated_group_still_readable`；变异 `ctxvar-treated-as-derived` |

变异负控扩到 **17 类**，复跑 **17/17 门能红**。

> **审查轮次说明（如实）**：round-2 与 round-3 均被外部内容过滤在收尾阶段中断，未产出完整的分级报告与合并裁定。两轮中断前给出的 **5 条**反证已全部核实并处置（3 条修复 + 1 条登记边界 + 1 条自查追加）。**因此"BLOCKER/HIGH 清零"目前只有 round-1 十三条 + round-2/3 五条的逐条闭合证据，没有一份完整的 round-2/3 终裁报告。** 这一点必须由用户知悉后决定是否补跑（见验收单 §六裁决点 5）。

## 未触碰（全批禁改，逐条确认）

`review_service.py` / `endpoints/review.py`（写移交条款）、`exam_service.py` / `verification_service.py`（G5-12 地盘）、`graphiti_memory_reader` / `graphiti_belief_service`（DEBT-12）。

> 注：`endpoints/exam_quick.py` **不在**禁改名单（名单里是 `exam_service.py`）。B-3 的修改限于该端点入口加解析 + 下传 group，未动出题逻辑。
