> 批次: BATCH-2026-09-05-第十二批 · 车道 Y6 · 卡 CARD-RED-TRIAGE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-TRIAGE.md)"`
> 审查绑定: `368b145a`（开工 SHA；本卡零代码改动，收工 HEAD 同）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**发现 2 项 HIGH：部分残余分类缺少排除回归的依据，下一批分派也尚未覆盖完整 247 条。** 全程只读，未改文件、未跑 pytest、未连接数据库。

本次以最终读到的[分诊表](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/2026-09-05-第十二批-tests-unit-红基线分诊-247.md)和[草案](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/2026-09-05-第十二批-RED-第十三批卡草案.md)为准，SHA256 前缀分别为 `ede1165d11e2`、`18efec5a35a5`。草案在审查期间发生更新，以下行号对应更新后版本。

**BLOCKER：未发现。**

1. **HIGH — 至少 5 条残余直接归为 C2，但证据不足以排除实现回归。**

   分诊表 **277–280 行**的四条 `test_vault_notes_group_filter.py`，实际失败包括：physics 查询仍返回 math、无匹配仍返回记录。表内现行实现指向 `vault_notes_retriever.py:227`，依据 SHA 均为 `—`。

   分诊表 **179 行**的 `test_strip_whiteboard_removes_admonition_callouts` 同样如此：日志证实正文未被剥离，表内仍指向现行 API，却没有契约演进依据。

   **最小改动：**补批准的契约变化及历史依据；补证前按本卡硬约束暂列“回归候选／新”，移交确认。这里认定的是**分类证据不足**；这些条目是否确为生产回归，**未验证**。

2. **HIGH — 分派未闭合：9 条“新”没有接收卡，C1 还漏计一条。**

   - 草案 **229–240 行**的 ENVDEP 只接原 B 转入的 3 条；**353–357 行**的 RED-R 只接 22 条回归候选。残余“新”9 条没有明确接收卡，位于分诊表 **75、76、77、109、119、120、140、166、276 行**。
   - C1 逐行实际为 **43 条**，草案 **249–257 行**仍写 `42 = 25+3+14`。漏掉的是分诊表 **74 行**：`test_cache_configuration.py::TestMemoryRetryDelayFromSettings::test_retry_delay_reads_settings`。
   - 排除撤销的 RED-B，当前实际是 **8 张修复卡＋1 张 RED-R 分析卡**；C2 总集合又包含 MOCKFIX 的 36 条。

   **最小改动：**补齐 `247 nodeid → 接收卡` 的唯一映射，纳入残余新 9 条及 C1 转入项，明确 C2 与 MOCKFIX 的统计关系，再冻结卡数。

3. **MEDIUM — nodeid 裁判方向正确，但缺少运行完整性条件。**

   草案 **63–67 行**将 pytest 输出直接过滤成失败集合，没有保留 pytest 退出状态及完整执行证明。异常中止、没有产生失败摘要时，集合比较可能显示“全部减少”。

   **最小改动：**在裁判说明中同时要求完整运行证据、原始日志及退出状态，再比较 nodeid。无需修改本卡代码。

4. **MEDIUM — 三条硬约束不能判为“全部在场”。**

   | 约束 | 核验 |
   |---|---|
   | A1：opt-in `authed_client`；禁 autouse／全局注入 key | **在场**，草案 69–72 行 |
   | B：纯虚构 vault；禁 ACTIVE_VAULT；禁 tests/unit 级 autouse | **不在场**；当前草案已撤销 B |
   | C1：无替代覆盖不许删；`xfail(strict=True)`＋reason | **在场**，草案 264–269 行 |

   **最小改动：**明确记录 B 撤销后原约束如何处置；若后继卡涉及 vault fixture，应明确继承这些约束。无需恢复已被证伪的 B 分类。

5. **MEDIUM — 当前净代码零差异成立，本卡开工至收工的证据链未验证。**

   当前 HEAD 为 `368b145a1a2155ae337302cb9f7088f658979e15`。工作区 diff、暂存区 diff 均为空；排除 `_bmad-output` 后，包含未跟踪文件的 status 也为空。

   但指定读取面内没有本卡实际开工 SHA 与收工差异记录。草案 **355 行**是下一张 RED-R 的占位判据，而且 commit-to-commit diff 不包含工作区、暂存区及未跟踪代码。

   **最小改动：**补实际开工／收工 SHA 与相应差异证据。现有证据支持“当前净代码无变化”，不足以证明历史全过程。

6. **LOW — 部分日志行号和旧正文仍需同步。**

   - 分诊表 **133、165、180 行**引用的 sentinel 块头均晚标 3 行；实际块头是日志 **1643、1967、2119**。
   - 草案 **105–113 行**仍统一归因于 lifespan／system router，但 **123–130 行**已经纠正为端点和服务捕获，前后冲突。
   - 四条 `test_graphiti_json_dual_write.py` 的表内测试行与日志调用帧不同：**264→290、146→176、424→458、391→415**。表内数字可能是定义行；对应源码不在读取面，**未验证**。

   **最小改动：**同步旧正文和日志定位；测试定义行与日志调用行分开标注。

独立复算及抽样结果如下。日志均指[开工运行日志](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-red-triage/unit-run-open-20260906T104910.txt)。

**基线、日志、分诊表三个集合完全一致：247 个唯一 nodeid，209 FAILED／38 ERROR／63 文件。** 247 条均找到对应失败块，表内改类标记实际为 119 条。当前最终分类是：

`A1-auth 37／sentinel 12／A2 3／C1 43／C2 109／E 9／真实现回归 22／新 12 = 247`

每类三个样本的核对记录：

| 类别 | 测试 file:line → 日志失败身份 |
|---|---|
| A1-auth | `test_chat_endpoint.py:274` → KeyError budget；`test_enrich_context_vault_isolation.py:132`、`test_study_question_deep_mode.py:65` → 503；均同块出现 auth 拒因 |
| A1-sentinel | detailed health `test_returns_components`、mock degradation `test_mock_mode_logs_warning`、review mode `test_fresh_mode_parameter_accepted` → 日志 1643／1967／2119 均为哨兵；表内源码行号未验证 |
| A2 | `test_sync_batch_auth.py:117`、`test_system_endpoint_auth.py:112/:161` → 均为 `500 == 503`，同块有 Settings ValidationError |
| 原 B，现已改类 | `test_memory_service_batch.py:46`、`test_story_30_11_batch_parallel.py:361`、`test_story_30_13_batch_idempotency.py:46` → fixture 阶段 MagicMock 不可 await，均到 `memory_service.py:381` |
| C1，三子类各一条 | `test_memory_service_write_retry.py:75` → 缺已删 API；`test_story_38_6_scoring_reliability.py:39` → `0.5 >= 2.0`；`test_story_38_4_dual_write_default.py:39` → default=False |
| C2 | `test_config_neo4j.py:22` → ValidationError；`test_supplementary_reranker.py:587/:653` → `1.0 == 0.7`／`None is True` |
| E | `test_agent_templates_smoke.py:73/:86/:94` → 缺 hint 模板／`11 >= 17`／缺 hint 模板 |
| 回归候选 | `test_agent_memory_injection.py:273` → 异常逃逸；`test_difficulty_canvas_integration.py:432` → AgentType NameError；`test_story_2_3_error_reminders.py:403` → 时间戳断言不符 |
| 新 | `test_agent_service_extraction.py:348` → True is False；`test_calibration_tracker.py:266` → 边界枚举不符；`test_difficulty_matcher.py:113` → False is True |

**抽样技术失败身份均有日志支撑，未发现需要靠读代码才能推断出来的失败身份。** 但“14 条没有测试 file:line”这一数字未复现：按失败块内是否出现同一测试文件的源码定位统计，是 **12 条 sentinel 没有定位**；另有上述 **4 条定位行不同**。两条缺 `mocker` 的 ERROR 有明确文件和行号。

A1 拆分成立：原 31 条 auth 的 `29 个状态断言＋2 个 KeyError` 对上，另 6 条 sync 异常分类用例也确实先被 auth 拦住。12 条 sentinel 全部有对应 owner=nodeid，两条残余改归正确。**漂移动摇的是固定 12 个成员跨运行稳定这一说法，不动摇本次失败身份及拆卡结论。** 第二轮“一增一减”和新增的单例因果机制，因缺第二轮证据及限定面外源码，均未独立验证。

题面中的 B 旧结论已经被当前文档撤回：38 个 ERROR 中，**36 个是 MagicMock 不可 await，2 个是缺 mocker**；全日志没有 `VaultScopeUnresolved`。不能再把这 38 条归因于作用域 fail-closed。

22 条回归候选均带嫌疑 SHA、nodeid 和触发／预期摘要；**已证实回归未验证**，草案也明确尚无 bisect。A2 的配置拒空 key 逻辑归于 `f718d040`，auth 硬化归于 `c9bb6c9a`，已用只读 Git 核实。E 的完整生产调用链及模板历史、部分 C1 删除历史不在限定读取面，未作独立背书。

**总评：这份分诊可以作为继续确认和拆卡的证据底稿，暂不能直接作为下一批固定“8 张卡”的完整派工依据。先补残余分类证据、247 条唯一接收映射和收工证据，再冻结卡单。**
