# CARD-EPW-COVERAGE 覆盖矩阵 — CARD-RED-C1 登记的 33 + 4 条缺口逐条承接

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-EPW-COVERAGE]` · 车道 `card-t10-red`
> 缺口来源（⛔ 按节名捞、不抄行号）：`_bmad-output/审查/evidence-b13/red-align-da690bf8.md`
> §三「CARD-RED-C1 —— 33 条，全部 skip 掩盖」代码块（33 条，sort 序）
> ＋ 同节「另：Y4-D 顺带关掉的 4 条『原本绿』」（4 条）。合计 **37**。
> 承接方枚举：`新文件` = `backend/tests/unit/test_episode_worker_coverage_epw.py`（本卡新增）/
> `已有 retry 测试` = `backend/tests/unit/test_episode_worker_retry.py`（参照，本卡不改）/
> `T10-C 已 un-skip 重写` = 前一卡 CARD-Y4-D-TAIL 恢复的 15 条 /
> `语义已删·无等价·登记退役`。
> nodeid 前缀 `tests/unit/` 省略；新文件用例名前缀 `test_episode_worker_coverage_epw.py::` 省略。

| # | 原 nodeid | 语义一句话 | 承接方 | 承接用例/依据 |
|---|---|---|---|---|
| 1 | `test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_exception_increments_counter` | dual-write 抛异常时失败计数器递增 | 新文件 | `test_exception_failures_increment_failure_counter_per_attempt`（计数器由模块级 `dual_write_failures` 迁为 `WorkerMetrics.episodes_failed`，逐次尝试各记一次；迁移如实声明于文件头 §5） |
| 2 | `test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_retry_failure_writes_dead_letter` | 重试耗尽后写死信条目 | 新文件 | `test_dead_letter_written_on_retry_exhaustion`（文件存在 + `episodes_dead_lettered==1` + 记录字段 name/group_id/request_id/error_type/failed_at） |
| 3 | `test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_timeout_increments_counter` | dual-write 超时时失败计数器递增 | 新文件 | `test_timeout_failures_increment_failure_counter_per_attempt`（`asyncio.TimeoutError` 4 次尝试 ⇒ `episodes_failed==4`、死信只记 1） |
| 4 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_config_flag_enables_dual_write` | 配置开关打开时启用 dual-write | T10-C 已 un-skip 重写 | CARD-Y4-D-TAIL 删除 `test_graphiti_json_dual_write.py` 模块级 `pytestmark` skip（本卡第 0 分钟实测 `grep -c 'pytestmark = pytest.mark.skip'` = 0） |
| 5 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_dual_write_called_after_neo4j_success` | Neo4j 写成功后才触发 dual-write | T10-C 已 un-skip 重写 | 同上 |
| 6 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_json_write_failure_doesnt_affect_main_flow` | JSON 写失败不影响主流程返回 | T10-C 已 un-skip 重写 | 同上 |
| 7 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_learning_memory_dataclass_creation` | LearningMemory dataclass 构造语义 | T10-C 已 un-skip 重写 | 同上 |
| 8 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_record_temporal_event_dual_write` | record_temporal_event 触发 dual-write | T10-C 已 un-skip 重写 | 同上 |
| 9 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_failure_logging` | 写失败的日志形态 | T10-C 已 un-skip 重写 | 同上 |
| 10 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_success_logging` | 写成功的日志形态 | T10-C 已 un-skip 重写 | 同上 |
| 11 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_timeout_logging` | 写超时的日志形态 | T10-C 已 un-skip 重写 | 同上 |
| 12 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exception_failure_warning_includes_error_message` | 异常失败的 warning 日志含错误消息 | 新文件 | `test_retry_warning_includes_attempt_number_and_error_message`（3 条 warning 各含 `str(error)` 与 `attempt i/3`） |
| 13 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exponential_backoff_all_failures` | 全部失败时退避序列 1.0s/2.0s | 新文件 | `test_backoff_upper_bound_series_is_1_2_4` + `test_all_attempts_exception_then_dead_letter`（定值 → full jitter **上界**序列，语义收窄声明见文件头 §1） |
| 14 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exponential_backoff_delays` | 退避延迟值 1.0s/2.0s | 新文件 | `test_backoff_upper_bound_series_is_1_2_4`（patch `random.uniform` 捕获实参 `(0,1)/(0,2)/(0,4)`）+ `test_backoff_upper_bound_is_monotonic_and_capped_at_60` |
| 15 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_mixed_timeout_then_exception_then_success` | 超时→异常→成功的混合重试链 | 新文件 | `test_mixed_timeout_then_exception_then_success`（3 次尝试、2 次退避、最终 processed） |
| 16 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_record_temporal_event_uses_retry_method` | 调用方 `record_temporal_event` 走的是带重试的写方法 | 语义已删·无等价·登记退役 | **被测符号**已删：`MemoryService._write_to_graphiti_json_with_retry` 随 `59586af1` (2026-03-26) 删除 ⇒ 针对该符号的这条用例无等价物，退役成立。⚠️ **收窄口径（Codex r1 MEDIUM-3 更正，原措辞过强）**：这**不等于**「调用方接线语义已消失」——`memory_service` 今天仍有 4 处 `get_episode_worker()`（`:462/:1540/:1821/:1957`），要为它写等价接线测试在技术上**是可行的**（`test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::ready_worker` 的「tmp_path worker + `monkeypatch.setattr` 替换工厂」就是现成范式）。本卡不写的理由是**地盘**：那属 `memory_service` 接线面，且 (c) 的三入口门禁止本卡直调单例。故本行的准确含义是「**旧符号退役 + 新接线覆盖移交、未验证**」，不是「缺口已闭合」 |
| 17 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_retry_creates_new_timestamp_each_attempt` | 每次重试新建记录（新 timestamp） | 新文件 | `test_retry_reuses_same_task_and_preserves_timestamps`（⚠️ 语义**反转**：现实现重新入队**同一** `EpisodeTask`，`created_at`/`reference_time` 不变，仅 `retry_count` 递增；按现实现钉死，声明见文件头 §4） |
| 18 | `test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_timeout_failure_warning_includes_timeout_suffix` | 超时失败的 warning 带 `(timeout)` 后缀以区分错误类型 | 新文件 | `test_all_attempts_timeout_then_dead_letter`（`error_type=="TimeoutError"`）+ `test_dead_letter_log_carries_error_type_not_error_message`（⚠️ 收窄：区分能力从文案后缀迁到死信记录 `error_type`；`TimeoutError` 的 `str()` 为空串，现 warning 无法承载该区分，声明见文件头 §3） |
| 19 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_all_retries_failed_warning_logging` | 全部重试失败后的 warning 日志 | 新文件 | `test_retry_warning_includes_attempt_number_and_error_message`（每次重试一条 warning）+ `test_dead_letter_log_carries_error_type_not_error_message`（耗尽后的 `logger.error`） |
| 20 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_exception_triggers_retry` | 非超时异常同样触发重试 | 新文件 | `test_non_timeout_exception_triggers_retry`（`ValueError` ⇒ 2 次尝试、1 次退避、零死信） |
| 21 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_first_success_debug_logging` | 首次成功只记 debug 不记 info | 新文件 | `test_enqueue_logs_debug_while_success_logs_info`（⚠️ 收窄：现 worker 对首次/重试成功用同一条 info，可区分的分级是「入队 debug / 处理完成 info」，声明见用例 docstring） |
| 22 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_retry_success_logging` | 重试成功后记 info 日志 | 新文件 | `test_enqueue_logs_debug_while_success_logs_info` + `test_success_after_one_retry`（重试后 `episodes_processed==1` 且成功路径落 `Episode processed` info） |
| 23 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_with_all_optional_params` | 所有可选参数逐项透传 | 新文件 | `test_all_optional_params_forwarded_to_add_episode`（entity_types/edge_types/source=json/reference_time/source_description + 影子分组字面量）+ `test_optional_params_omitted_when_unset`（未设不得以 None 透传） |
| 24 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_fails_after_all_retries_exception` | 异常耗尽全部重试后失败 | 新文件 | `test_all_attempts_exception_then_dead_letter`（4 次尝试 → 死信，`error_type=="RuntimeError"`） |
| 25 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_fails_after_all_retries_timeout` | 超时耗尽全部重试后失败 | 新文件 | `test_all_attempts_timeout_then_dead_letter`（4 次尝试 → 死信，`retry_count==3`） |
| 26 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_after_one_retry` | 一次失败后重试成功 | 新文件 | `test_success_after_one_retry`（2 次尝试、1 次退避、`episodes_failed==1`） |
| 27 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_after_two_retries` | 两次失败后第三次成功 | 新文件 | `test_success_after_two_retries`（3 次尝试、2 次退避、`episodes_failed==2`） |
| 28 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_first_attempt` | 首次尝试即成功 | 新文件 | `test_first_attempt_success_no_retry`（`await_count==1`、`retry_count==0`、无死信文件）。⚠️ 如实：`test_episode_worker_retry.py::test_basic_enqueue_and_process` 也已断言 `await_count==1` 与 `episodes_failed==0`（后者同样蕴含零重试）；本卡用例的增量只是**对象级**不变量 `task.retry_count == 0`（计数器口径之外再钉任务自身）与 `not dead_letter.exists()` 的组合 |
| 29 | `test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_zero_retries_single_attempt` | `max_retries=0` 只尝试一次 | 新文件 | `test_zero_max_retries_single_attempt_then_dead_letter`（`can_retry is False`、零退避、立即死信且 `retry_count==0`） |
| 30 | `test_qa_38_6_scoring_reliability_extra.py::TestFullCycleIntegration::test_full_cycle_fail_record_recover_merge` | 失败 → 记账 → 恢复 → 合并视图 全循环 | 新文件 | `test_dead_letter_record_is_replayable_without_full_body` + `test_dead_letter_store_count_matches_appended_lines`（⚠️ **只承接记账半程**：sha256/length/reference_time/source_description 等重放所需字段 + `count()` 计数；「恢复→合并视图」半程属 `MemoryService.recover_failed_writes`/`load_failed_scores` 面，不在 worker 内，本卡不覆盖——见验收单「本卡未证明什么」） |
| 31 | `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_malformed_entries_preserved` | 畸形条目保留不丢 | T10-C 已 un-skip 重写 | CARD-Y4-D-TAIL 删除该类类级 skip（本卡第 0 分钟实测 `grep -c '@pytest.mark.skip'` = 0），并按 `_enqueue_episode → GraphitiEpisodeWorker` 管线重写 |
| 32 | `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_partial_failure` | 部分失败时的 recovered/pending 计数 | T10-C 已 un-skip 重写 | 同上 |
| 33 | `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_successful_replay` | 成功重放后条目从文件移除 | T10-C 已 un-skip 重写 | 同上 |
| 34 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_config_flag_disables_dual_write`（原本绿） | 配置开关关闭时禁用 dual-write | T10-C 已 un-skip 重写 | 模块级 skip 已删（同 #4） |
| 35 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_fire_and_forget_doesnt_block_return`（原本绿） | fire-and-forget 不阻塞返回 | T10-C 已 un-skip 重写 | 同上 |
| 36 | `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_timeout_protection`（原本绿） | 超时保护存在 | T10-C 已 un-skip 重写 | 同上 |
| 37 | `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_no_file`（原本绿） | 无 fallback 文件时早退返回零 | T10-C 已 un-skip 重写 | 类级 skip 已删（同 #31）；该用例不需 worker，走 recover 早退分支 |

## 统计（脚本自校：`coverage_matrix_check.py`）

- **新文件承接 N1 = 21**（#1 #2 #3 #12 #13 #14 #15 #17 #18 #19 #20 #21 #22 #23 #24 #25 #26 #27 #28 #29 #30）
- **已有 retry 测试承接 N2 = 0** —— 本卡对这 21 行**逐条都写了**新用例，故承接方一律记新文件；
  `test_episode_worker_retry.py` 的同向用例在「承接用例/依据」列作交叉引用，不另计承接，
  避免一条缺口被两处重复记账。

  ⚠️ **与参照文件的重叠度（Codex r1 LOW-1 更正——原措辞「剩余 14 行参照文件均未触及」不成立，
  逐行数过后重写）**。参照文件共 **5 个**用例（`grep -c 'def test_'` 实测 = 5）：
  `test_basic_enqueue_and_process` / `test_exponential_backoff_sleep_series` /
  `test_dead_letter_on_retries_exhausted` / `test_worker_metrics_completeness` /
  `test_request_id_propagation_through_episode_task`。逐行比对结果：

  ⚠️ **本表在 Codex r2 LOW-3 后重数过一遍**（原版把 #1 说成「只有不等式」、把 #20 列进「未触及」，
  两处都不实——参照文件 `test_dead_letter_on_retries_exhausted` 已有 `episodes_failed == 4` 的**等式**，
  `test_exponential_backoff_sleep_series` 的失败形态就是 `RuntimeError` 即已覆盖「非超时异常触发重试」）。

  | 重叠程度 | 行号 | 计 | 说明 |
  |---|---|---|---|
  | **同题**（参照文件已有直接断言） | #1 #2 #13 #14 #20 #24 #28 #30 | 8 | #1/#2/#24/#30 落在 `test_dead_letter_on_retries_exhausted`（`await_count == 4`、`episodes_failed == 4`、`episodes_dead_lettered == 1`、sha256/length/截断正文）；#13/#14/#20 落在 `test_exponential_backoff_sleep_series`（3 次 `RuntimeError` → 重试 → 第 4 次成功 + 三段退避区间）；#28 落在 `test_basic_enqueue_and_process` |
  | **部分同题**（形态更窄／不等式／只覆盖一部分字段） | #3 #18 #23 #25 #26 #27 | 6 | #3 的超时形态参照文件没有（它只用 `RuntimeError`）；#18 参照文件只断言单一 `error_type == "RuntimeError"`，没有「超时 vs 异常如何区分」的对照；#23 只覆盖 name/group_id/episode_body 三个 kwarg，未覆盖 entity_types/edge_types/source；#25 的错误形态是 `RuntimeError` 不是超时；#26/#27 参照文件只有「3 次失败后成功」这一种，没有**一次**/**两次**重试的确切尝试数 |
  | **未触及** | #12 #15 #17 #19 #21 #22 #29 | 7 | 日志分级三条（#12 #19 #21 #22 中的 #12/#19/#21/#22 —— 参照文件**零**日志断言）、混合错误类型（#15）、重试身份与时间戳（#17）、`max_retries=0`（#29） |

  （8 + 6 + 7 = 21 ✅ 与 N1 对齐。）

  新文件相对参照文件的增量，逐条不同：#13/#14 由「区间采样（下界允许 0，也允许 `cap/2`）」升为
  「`random.uniform` **实参 `(0, cap)` 的等值断言**」，并新增**实际重试链路**的抽样区间 + 实际 sleep 值断言；
  #3/#25 补超时形态与 `error_type` 对照；#23 补三个可选参数与「未设不得以 None 透传」；
  #1 把「耗尽路径的 4」扩到「部分失败路径的 2」；#12/#19/#21/#22 是**参照文件完全没有**的日志分级面；
  #17 是对象身份 + 时间戳不变量；**#28 的增量最小**，只多了对象级 `task.retry_count == 0`
  （参照文件的 `episodes_failed == 0` 已蕴含零重试）；#2/#30 的增量是 `count()` 与 `request_id` 的组合断言。
- **T10-C 已 un-skip 重写 = 15**（#4–#11 共 8 + #31–#33 共 3 + #34–#37 共 4）
- **语义已删·无等价·登记退役 N3 = 1**（#16，删除 sha `59586af1`）
- **N1 + N2 + 15 + N3 = 21 + 0 + 15 + 1 = 37** ✅

## 附录 A — `test_story_38_6_scoring_reliability.py` 三条 xfail 的去标决策（不计入上表 37 行）

> 这三条不是 CARD-RED-C1 的 33+4 缺口，而是 RED-C1 给它们打的 `@pytest.mark.xfail(strict=True)`
> 且 reason 写死 `CARD-EPW-COVERAGE`。决策程序见卡文 §〇 口径更正 2：(A) 改写对齐真 worker 使其 PASS 后去标 /
> (B) 主题永久删除 ⇒ 删除桩用例并在此登记承接。⛔ 两者都不碰 `backend/app`。

| 原用例 | 断言的东西 | 决策 | 依据 / 承接 |
|---|---|---|---|
| `TestAC1TimeoutRetryAlignment::test_inner_per_attempt_timeout_increased` | 模块级本地桩 `GRAPHITI_JSON_WRITE_TIMEOUT >= 2.0`（桩值 0.5 ⇒ 恒假） | **B（删除）** | 现 worker **对 `add_episode` 不加任何超时包装**：`_process_episode` 直接 `await self._graphiti.add_episode(**kwargs)`，全文件 `asyncio.wait_for` 只出现在连通性探针与 `stop()` 排空（实测 `grep -n 'wait_for' backend/app/services/episode_worker.py` → 366/480 两处，均非每次尝试超时）。该语义**无等价**，不伪造；退役理由与 #16 同源（`59586af1`） |
| `TestAC1TimeoutRetryAlignment::test_retry_backoff_base_is_1_second` | 模块级本地桩 `GRAPHITI_RETRY_BACKOFF_BASE == 1.0`（桩值 0.1 ⇒ 恒假） | **A（改写对齐真 worker）** | 改为断言 `EpisodeTask.backoff_seconds` 的**上界基数**：`retry_count=0` 时退避区间是 `[0, 1]`（patch `random.uniform` 捕获实参），与旧「base=1.0s」同值；名实一致（函数名仍是「退避基数为 1 秒」） |
| `TestAC1TimeoutRetryAlignment::test_backoff_progression` | 模块级本地桩推导的 `[1.0, 2.0, 4.0]` 序列 | **A（改写对齐真 worker）** | 改为断言真 worker 的上界序列 `[1, 2, 4]`（`min(2**retry_count, 60)`），并钉 60s 封顶；与新文件 `test_backoff_upper_bound_series_is_1_2_4` 同源语义、互为双保险 |

## 附录 B — 新文件用例清单（**33 个测试函数**，参数展开后 **47 条**，171 条 assert）

> ⚠️ 本节数字被 Codex 连纠两轮，现按**终稿**实测重写：
> - r1 LOW-1：原先写「26 条」，那是写卡时的计划数、不是实测数；
> - r3 LOW-3：r2 时写的「32 函数 / 46 条 / 161 assert」在 r3 加了一个用例后未同步。
>
> 终稿实测口径：`ast` 数出 **33** 个 `test_` 函数、**171** 条 `assert`；
> （⚠️ Codex r5 LOW-5：`169` 是 r4 时的数，r5 整改又加了断言没同步；本行为收工重取值。）
> `pytest --collect-only` 收集到 **47** 条（3 个参数化用例分别展开 6/6/5）。
> 三笔代码 commit 的用例数轨迹：31 →（r1 HIGH-1）32 →（r2 LOW-1）33。

A 组 重试与尝试次数（8）：`test_first_attempt_success_no_retry` / `test_success_after_one_retry` /
`test_success_after_two_retries` / `test_all_attempts_timeout_then_dead_letter` /
`test_non_timeout_exception_triggers_retry` / `test_all_attempts_exception_then_dead_letter` /
`test_zero_max_retries_single_attempt_then_dead_letter` / `test_mixed_timeout_then_exception_then_success`

B 组 退避（3）：
- `test_backoff_upper_bound_series_is_1_2_4` —— 属性层：`random.uniform` 实参 = (0,1)/(0,2)/(0,4)
- `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` —— **实际重试链路**（函数名保留历史，
  断言已随 Codex 两轮收紧而升级）：① 抽样区间实参 = `[(0,2),(0,4),(0,8)]`（下界 0 = full jitter
  未被削半，且 `retry_count` **先递增** ⇒ 是 2/4/8 不是 1/2/4）；② 传给 `asyncio.sleep` 的值
  == `random.uniform` 返回的**哨兵串** `[0.37, 1.23, 4.56]`（与区间无函数关系 ⇒
  「保留抽样调用但按区间重算 sleep 值」的写法得不到它们 —— Codex r1 HIGH-1 + r3 MEDIUM-1）
- `test_backoff_upper_bound_is_monotonic_and_capped_at_60` —— 上界单调 + 60s 封顶，
  并断言**属性返回值 == 抽样值**（防二次截断，Codex r3 LOW-1）

C 组 死信（3）：`test_dead_letter_written_on_retry_exhaustion` /
`test_dead_letter_record_is_replayable_without_full_body` / `test_dead_letter_store_count_matches_appended_lines`

D 组 确定性错误（1）：`test_deterministic_validation_error_skips_retry_and_dead_letters`

E 组 隐私（6）：`test_dead_letter_omits_full_body_by_default` /
`test_dead_letter_stores_redacted_full_body_when_flag_enabled`（6 参数） /
`test_dead_letter_full_body_flag_rejects_non_truthy_values`（6 参数） /
`test_dead_letter_error_message_is_redacted_and_truncated` /
`test_redact_scrubs_known_secret_patterns`（5 参数） / `test_redact_is_noop_for_non_strings_and_clean_text`

F 组 计数（6）：`test_timeout_failures_increment_failure_counter_per_attempt` /
`test_exception_failures_increment_failure_counter_per_attempt` / `test_metrics_snapshot_covers_all_counters` /
`test_worker_metrics_to_dict_serializes_nonzero_depth_and_times`（**Codex r2 LOW-1 新增**：喂已知样本
求值 `queue_depth=7` / `avg=1000.0` / `max=1500.0` + 100 条滑窗，防 `to_dict()` 把这些字段写死成 0）/
`test_queue_full_drops_and_counts` / `test_enqueue_after_stop_returns_false`

G 组 日志（3）：`test_retry_warning_includes_attempt_number_and_error_message` /
`test_dead_letter_log_carries_error_type_not_error_message` / `test_enqueue_logs_debug_while_success_logs_info`

H 组 参数透传（2）：`test_all_optional_params_forwarded_to_add_episode` / `test_optional_params_omitted_when_unset`

I 组 重试身份（1）：`test_retry_reuses_same_task_and_preserves_timestamps`

> F 组的 `test_queue_full_drops_and_counts` / `test_enqueue_after_stop_returns_false` 覆盖的是
> `enqueue` 的 `QueueFull` / `QueueShutDown` 两条拒绝分支（`episodes_dropped_queue_full` 是
> `WorkerMetrics` 六计数器之一）。它们**不对映** 33+4 里的任何一条，属本卡顺带补的真实分支，
> 不计入上表任何承接列。
