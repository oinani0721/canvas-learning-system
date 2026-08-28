# CARD-G4-2 Codex round-1 整改记录

> **审查存档**: `codex-review-CARD-G4-2.md`（gpt-5.6-sol / ultra / read-only）
> **round-1 裁定**: 需整改，不可合并 — 4 BLOCKER + 6 HIGH + 4 MEDIUM + 2 LOW
> **整改日期**: 2026-08-28

## 审查抓到的根本缺陷（值得单独记一笔）

我的首版方案有一个**方法论错误**：只在「异常被抛出」这条路径上埋了信号
（`try/except` + `fail_sink`）。但生产环境最常见的故障形态恰恰**不抛异常**：

- `Neo4jClient` 初始化失败或运行中降级后进入 **JSON_FALLBACK** 模式——
  `initialized` 仍为 True、Cypher 正常返回 `[]`、无任何异常；
- `GraphitiClient` / `LanceDBClient` 以 `enable_fallback=True` 创建，
  超时和错误在**客户端内部**被吞成空列表，且 `initialize()` 返回的 False
  被调用方丢弃，失败实例仍被发布为 singleton（此后永久假空，且恢复后不重连）。

结果就是：我的 `except` 永不触发 → `fail_sink` 恒空 → 四态照旧报 `ok/empty`。
**测试全绿，生产照样假装空结果**——正是本卡要根治的病，换了个地方复发。

修法是把检测从「捕获异常」改为「**探测后端健康**」：新增
`_neo4j_backend_failure()` 在每次查询前检查 fallback 模式 / 初始化状态 /
health_status，并让 singleton 发布以 `initialize()` 成功为前提。

## 处置总表

| # | 级别 | 问题 | 处置 | 证据 |
|---|------|------|------|------|
| 1 | BLOCKER | Neo4j JSON_FALLBACK 被当健康空结果，还污染 30s/5min 缓存 | **已修** — 新增 `_neo4j_backend_failure()` 探针，接入 fulltext / learning_history / score_history / subgroup 四个检测点；降级时不入缓存 | `TestSilentBackendFailover` 6 条 |
| 2 | BLOCKER | Graphiti/LanceDB 客户端内部吞错，`initialize()->False` 被忽略，失败实例进 singleton | **已修** — 初始化失败不发布 singleton（下次调用重试）并抛出，由节点记入 `channel_errors` | `test_init_false_does_not_publish_singleton`、`test_init_false_surfaces_as_channel_error` |
| 3 | BLOCKER | `memory_degraded` 链断裂：`mastery_injection` 调旧 list 方法，状态被剥成 `.items`；空+故障被判「真空、reason=None」 | **已修** — 改调 `search_memories_with_status()`，helper 返回 `(items, reason)`；unavailable → 走降级路径，degraded+空 → 带 `service_` 前缀原因 | `TestMemoryDegradedChain` 4 条（含反向锁：真空仍 reason=None） |
| 4 | BLOCKER | 三条读路径仍裸返回：`get_concept_history` 无状态键、`get_review_suggestions` 裸 list、`search_error_memories` 调旧 wrapper | **已修** — dict 路径加性状态键；两条 list 路径按同一「`*_with_status` + 旧方法委托」形态拆分 | 46 条测试通过 |
| 5 | HIGH | 状态判定用**过滤后**条目数，`min_relevance` 滤光结果会把 degraded 误升 unavailable；子组枚举失败与主 Tier 失败混为一谈 | **已修** — 记录过滤前候选数，状态只看源可用性；`tier_failures`（硬失败）与 `coverage_failures`（覆盖收窄）分离 | `test_low_score_results_filtered_out_still_degraded_not_unavailable`（正是我原测试用高分规避的场景）、`test_coverage_failure_alone_is_degraded_not_unavailable` |
| 6 | HIGH | 异常白名单不全，`neo4j.ServiceUnavailable` / `SessionExpired` / `openai.APIConnectionError` 可穿透四态方法 | **已修** — 五处边界改为捕获 `Exception` 并**显式保留 `CancelledError`** 语义 | ruff + 现有套件 |
| 7 | HIGH | LanceDB 跨学科：bridge 失败静默退回；`channel_errors` 建在其后无处可记；外层 except 把已获结果清空 | **已修** — 字典提到 bridge 之前；bridge 各失败分支记 `lancedb_cross_subject`；结果列表在 try 外初始化以保留部分成功 | `TestFusionStatusFolding::test_coverage_only_failure_is_degraded` |
| 8 | HIGH | 融合层无 attempted 通道模型：任一通道报错 + 总数 0 就判 unavailable，即使另一通道健康地查到 0 条 | **已修** — 区分主通道（graphiti/lancedb）与覆盖类键；`unavailable` 只在**所有主通道均失败**时成立 | `TestFusionStatusFolding` 5 条 |
| 9 | HIGH | `get_weak_concepts_with_status` 忽略 `LearningMemoryClient.initialize()` 返回的 False | **已修** — 检查布尔值，False → unavailable（未动客户端对外契约） | `test_initialize_returning_false_is_unavailable` + 反向锁 |
| 10 | HIGH | 注入测试证明力不足（`localhost:1` 从未真正连接、只替换私有方法、节点测试单薄） | **部分修** — 补齐静默降级（6 条）、singleton 门（2 条）、融合折算（5 条）、memory_degraded 整链（4 条）；`localhost:1` 用例保留但**降级为形态用例**并在卡文如实标注其局限 | 见下方诚实声明 |
| 11 | MEDIUM | `add_dicts` 跨轮次保留旧错误；multi-query 同键 last-write-wins | **未修，登记 followup** — 需要 per-attempt 分桶或 fan-out 前 reset，属 state 结构改造，超出本卡「只改服务层返回结构」边界 |
| 12 | MEDIUM | `StatusedResult` 只校验 reason，`OK+[]`、`EMPTY+[item]`、`UNAVAILABLE+[item]`、非 str reason、`items.append()` 均可绕过 | **已修** — 补齐载荷不变量校验 + 构造时复制隔断外部引用；`from_items(None)` 改为拒绝 | `TestStatusedResultContract` 新增 7 条 |
| 13 | MEDIUM | `get_learning_history` 对任何捕获到的失败固定报 degraded，未看本地兜底是否可信 | **未修，登记 followup** — 需要 fallback readiness/provenance 追踪（`_episodes_recovered` 冷启动态），属 A7 outbox/恢复面 |
| 14 | MEDIUM | `conversation_archive` 检索前永久置 `_initialized=True`，一次故障空列表令本进程不再恢复 archive markers | **未修，登记 followup** — 属调用方适配（清单 A 第 2 项），本卡边界是「服务层返回结构」 |
| 15 | LOW | `worst_status` 语义与四态定义冲突（`OK+UNAVAILABLE→UNAVAILABLE`，但有健康结果时整体应为 DEGRADED），且测试锁死了错误规则 | **已修** — 更名 `max_severity()`（明确只做组件级严重度排序）+ 新增 `fold_overall_status()` 做整体折算 | `TestMaxSeverity` + `TestFoldOverallStatus` 5 条 |
| 16 | LOW | 枚举/Literal 契约只覆盖 CanvasRAGState，`ScoreHistoryResponse.status` 等自由字符串镜像仍可漂移 | **未修，登记 followup** — 建议 G4-3 统一序列化 helper 时一并收 |

## 整改过程中自查发现的二次缺陷（诚实记录）

修 BLOCKER-1 时我引入的探针 `_neo4j_backend_failure()` 最初用 **truthy 判断**：

```python
if getattr(client, "is_fallback_mode", False):   # ← 错
```

真实 `Neo4jClient` 的这个属性是 `bool`，但**测试里的 `MagicMock` 属性是 truthy 的
Mock 对象**。结果全量回归里 11 条既有测试变红——探针把每个「未显式声明健康」的
mock 都判成了降级。

这是 fail-closed 用错了地方：**「看不懂这个客户端」不等于「这个客户端坏了」**。
前者只能放行（否则探针自己变成假警报源），后者才该拒绝。修正为要求可证的类型：

```python
if getattr(client, "is_fallback_mode", False) is True:   # 严格 True
stats = getattr(client, "stats", None)
if isinstance(stats, dict):                              # 只信真 dict
    if stats.get("initialized") is False: ...
    if isinstance(health, str) and health.lower() not in (...): ...
```

修正后 11 条恢复，且 JSON_FALLBACK 的真实降级仍被正确捕获
（`TestSilentBackendFailover` 6 条锁死双向行为）。

## 诚实声明：测试证明力的已知边界

Codex HIGH-10 指出 `TestRealUnreachableBolt` 的 `bolt://localhost:1` 用例
**并未真正发起连接**——生产代码在 `initialized=False` 处就短路了。这条批评成立。

该用例保留，但其价值已重新定位：它证明的是「客户端不可用时读路径返回
unavailable/degraded 而非 ok/empty」，**不是**「真实网络连接失败被正确处理」。
真正的连接层故障验证需要真库容器（7692），属 integration 门，本卡未做。
新增的 `TestSilentBackendFailover` 才是覆盖生产主流故障形态（JSON_FALLBACK）的用例。

## followup 汇总（4 项）

1. **`add_dicts` 跨轮次错误累积**（MEDIUM-11）— 需 per-attempt 分桶。
2. **`get_learning_history` 的 fallback readiness**（MEDIUM-13）— 冷启动/未恢复时应为 unavailable。
3. **调用方适配**（MEDIUM-14 + 清单 A）— `conversation_archive` 优先（`_initialized` 永久置位有重复归档风险）；`archive_scheduler` / `conversation_inheritance` / `learning_context` / mcp `memory_tools` 次之。
4. **其余三检索通道吞点**（`multimodal` / `cross_canvas` / `vault_notes`，在 `retrievers/` 子模块）+ 状态字符串镜像统一（LOW-16）。

## 边界遵守

`LearningMemoryClient` 对外契约冻结（仅在调用方检查其 `initialize()` 返回值，未改客户端）；
`exam_service.py` / `verification_service.py` 未触碰；`review.py` / `review_service.py` 未触碰。
