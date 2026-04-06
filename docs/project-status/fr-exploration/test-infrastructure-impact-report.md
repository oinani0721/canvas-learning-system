# 后端测试基础设施瘫痪对调试能力的影响报告

> **生成日期**: 2026-04-06
> **触发背景**: FR-KG-04 修复 session 的 pre-push 预跑发现大规模 unit test 失败
> **关联 change**: `openspec/changes/fix-structlog-caplog-compat/`
> **调研方式**: Claude Code 单独 agent 深度探索（high effort）
> **报告目的**: 向 ChatGPT Deep Research 提供完整的测试现状 + 3 层 hook 静默失效证据，以便它给出针对性的修复建议

---

## 一、实际数字（经 pytest 实测）

```
169 failed + 87 errors + 2212 passed
─────────────────────────────────────
共 2468 unit 测试
~10.4% 失败率
~89.6% 通过率
执行时间 65 秒
```

> 之前用户提到的 "298 测试失败" 实际是 **256**（169 failed + 87 errors）；剩下 42 条差额可能来自上次 session 截断的某次跑或包含 integration 测试的统计。

---

## 二、失败构成（不只是 caplog 一个根因）

| 类别 | 数量 | 触发原因 |
|------|------|---------|
| **caplog 空** | ~50 | `PrintLoggerFactory` 走 stdout 不走 stdlib，`caplog.records` 永远是 `[]` |
| **structlog 位置参数误用** | ~45 | 旧 `logger.info("msg", arg1, arg2)` 不兼容 → `BoundLoggerBase._proxy_to_logger() takes 2-3 args but 6 were given` |
| **Stale AttributeError** | ~40 | 测试引用已删除的方法/常量：`MemoryService._write_to_graphiti_json_with_retry`、`DUAL_WRITE_DEAD_LETTER_PATH` 等 |
| **AsyncMock 缺失** | ~25（87 errors 中绝大多数） | fixture 用 `MagicMock` 模拟 `await neo4j.get_all_recent_episodes(...)` → `'MagicMock' object can't be awaited` |
| **真断言失败** | ~10 | `test_calibration_tracker` 边界 off-by-one、其他算法回归 |

> 项目内实际查到 **54 个服务**已迁移到 `structlog.get_logger`（proposal 写的 47 是低估）。
> 病根位置：`backend/app/middleware/logging_middleware.py:43` 的 `PrintLoggerFactory`。

---

## 三、当前失去的调试能力

| 能力 | 状态 |
|------|------|
| `pytest -x` 在第一处真 bug 停止 | ❌ 会先撞上 169 个旧失败 |
| `pytest --lf` 重跑上次失败 | ❌ `--lf` 报告 256 条噪音 |
| `pytest -k <模式>` 定向跑 | ⚠️ 仅对未影响服务有效 |
| `caplog.records` 断言日志输出 | ❌ 全部 47+ 服务失效 |
| **Stop hook 阻断错误代码** | ❌ **静默失效**——`stop-test-runner.js` 用裸 `python` 而非 `.venv/bin/python`，`No module named pytest`，正则匹配不到 FAILED → 永远 exit 0 |
| **PostToolUse 影响域测试** | ❌ **静默失效**——`post-tool-router.sh:37` 把 pytest 输出 pipe 进 `tail -20`，`$?` 检查的是 `tail` 不是 pytest |
| **pre-push backend-smoke** | ❌ **静默失效**——`lefthook.yml:157` 同样 `2>&1 \| tail -5` 吞掉 pytest exit code |
| TDD 红绿循环 (`/tdd-cycle`) | ❌ 写的失败测试若打到 47 个服务之一就跑不动 |
| coverage 报告 | ⏭️ 已主动 `--no-cov`，无视 |

> **关键发现**：3 层 hook 防御（Stop / PostToolUse / pre-push）**全部已被静默绕过**——这不是 structlog 引起的，是 hook 脚本本身在 commit `f4d10d8` 前后的 pipe + venv 错误。

---

## 四、完全失明的服务（几乎所有测试都坏了）

| 服务 | 测试数 | 通过数 | 可用率 |
|------|--------|--------|--------|
| **memory_service** | 26 | 3 通过 / 20 failed / 6 errors | **11.5%** |
| **prompt_registry** | 33 | 5 通过 / 4 failed / 24 errors | **15%** |
| **agent_service** | 86 | 71 通过 / 13 failed / 2 errors | 83%（但所有 neo4j_memory + comparison 子集失明）|
| **batch_orchestrator (Story 30 系列)** | 27 | 0 通过 / 全部 errors | **0%** |

---

## 五、Unit 层从未被覆盖的关键服务

这些服务在 `backend/tests/unit/` 下**没有任何对应的 `test_*.py` 文件**：

- `sync_service` —— 仅 integration 覆盖（且 integration 默认不跑）
- `rag_service` —— 仅 `test_rag_multimodal_integration.py` 9 条（其中 3 条 FAILED）

---

## 六、仍可信的服务/测试区域

- **canvas_service** — 21/21 通过（包括 `add_edge` 和 `_sync_edge_to_neo4j`）
- **canvas_edge_sync / canvas_edge_bulk_sync / canvas_service_concurrency** — 34/34 通过
- **verification_service** — 19/22 通过（核心未坏，仅注入日志断言失明）
- **subject_resolver, fsrs_manager, neo4j_client（除 caplog 子集）, websocket_manager 等不依赖 caplog 的纯逻辑** — 仍可用
- 整体 **2212/2468 ≈ 89.6%** 测试仍能跑过（绝大多数因为没用 caplog，也没用 AsyncMock 模拟 neo4j）

---

## 七、6 个具体调试场景能否用测试验证

| # | 场景 | 能否验证 | 原因 |
|---|------|---------|------|
| A | verification `_get_rag_context_for_concept` 字段映射（刚修复） | ❌ 不能 | `tests/unit` 搜不到该方法名；间接的 `test_verification_dedup` 和 `test_verification_service_*` 有 5 条已坏 |
| B | sync_service `_upsert_edge` Cypher | ❌ 不能 | `tests/unit` 没有任何 `test_sync_service*` 文件，仅 integration 覆盖 |
| C | agent_service LLM 调用流 | ⚠️ 部分 | 84 测试中 71 通过；neo4j_memory 6 条全失明、comparison 6 条全失明 |
| D | memory_service concept score 持久化 | ❌ 不能 | `test_memory_service_batch.py` 6 条 `TestRecordBatchLearningEventsConcept` 全 ERROR；`test_memory_service_write_retry` 18 条全 FAILED |
| E | canvas_service.add_edge fire-and-forget | ✅ 可以 | `test_canvas_edge_sync.py` + `test_canvas_service_concurrency.py` 34/34 通过 |
| F | rag_service.query state building | ❌ 不能 | `tests/unit` 没有任何 `test_rag_service*` 文件；仅 `test_rag_multimodal_integration.py` 9 条中 3 条 FAILED |

---

## 八、一句话底线

**89.6% 的测试还能跑过**，但你最关键的 3 个服务——`memory_service` / `batch_orchestrator (Story 30 全系列)` / `prompt_registry`——**已基本失明**，`sync_service` 和 `rag_service` 在 unit 层**从未被覆盖**；3 层 hook 防御因为 `tail` 吞 exit code + 裸 `python` 找不到 pytest，**全部静默失效**——AI agent 改坏代码**不会被任何自动化拦住**。

---

## 九、关键文件路径（供 ChatGPT Deep Research 定位）

### 病根
- `backend/app/middleware/logging_middleware.py:43` —— `PrintLoggerFactory` 配置

### 已规划的结构修复
- `openspec/changes/fix-structlog-caplog-compat/proposal.md`
- `openspec/changes/fix-structlog-caplog-compat/design.md`
- `openspec/changes/fix-structlog-caplog-compat/tasks.md`
- `openspec/changes/fix-structlog-caplog-compat/specs/backend-logging/spec.md`

### 静默失效的 hook 脚本
- `.claude/hooks/stop-test-runner.js:34` —— 裸 `python` 不是 venv 里的
- `.claude/hooks/post-tool-router.sh:37` —— `tail -20` 吞 exit code
- `lefthook.yml:157` —— `tail -5` 吞 exit code

### 最严重失明的测试文件
- `backend/tests/unit/test_memory_service_write_retry.py` (18 failed)
- `backend/tests/unit/test_prompt_registry.py` (4 failed + 24 errors)
- `backend/tests/unit/test_story_30_11_batch_parallel.py` (10 errors)
- `backend/tests/unit/test_story_30_13_batch_idempotency.py` (11 errors)
- `backend/tests/unit/test_agent_templates_smoke.py` (9 failed)
- `backend/tests/unit/test_graphiti_json_dual_write.py` (8 failed)

---

## 十、本报告对 ChatGPT Deep Research 的用途

1. **锁定"修 structlog" 只能解决 ~50 个失败**，剩下的 206 个（structlog 位置参数误用 + Stale AttributeError + AsyncMock 缺失 + 真断言失败）需要**独立的 5 条修复路径**
2. **"修 structlog" 不能自动修复 3 层 hook 静默失效** —— hook 修复是**平行任务**
3. **`sync_service` 和 `rag_service` 的 unit 层空白**是一个结构性缺陷——这是需要**全新补测试**而不是"修旧测试"
4. **3 个完全失明的服务**需要优先恢复测试可见性，否则后续的任何 bug 修复都是盲飞
5. **89.6% 可通过率**可能掩盖"关键服务失明"的真实风险 —— Deep Research 不应被这个表面数字误导

