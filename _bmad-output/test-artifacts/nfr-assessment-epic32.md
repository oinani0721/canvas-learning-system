# NFR Assessment - EPIC-32 Ebbinghaus Review System Enhancement (FSRS-4.5 Integration)

**Date:** 2026-02-11
**Story:** EPIC-32 (Stories 32.1-32.4, 32.6-32.7, 32.10-32.11)
**Overall Status:** CONCERNS ⚠️

---

Note: This assessment summarizes existing evidence; it does not run tests or CI workflows.

## Executive Summary

**Assessment:** 5 PASS, 3 CONCERNS, 0 FAIL

**Blockers:** 0

**High Priority Issues:** 2 (测试隔离 P0, Story 32.4 覆盖率 P0)

**Recommendation:** 有条件通过。核心 FSRS 功能实现完整且可靠，但测试质量存在结构性问题（隔离维度 24/100 Grade F）。建议修复 P0 测试隔离问题后再进入 release gate。

**与上次评估差异 (2026-02-10 → 2026-02-11):**
- 测试审核评分: 91/100 (A-) → **61/100 (D)** — 5维度评估发现隔离维度严重不足
- Testability: 4/4 → **3/4** — module-scoped fixture 是可量化缺陷
- 总分: 25/29 → **24/29** — 降级 1 分

---

## Performance Assessment

### Response Time (p95)

- **Status:** PASS ✅
- **Threshold:** FSRS 计算 < 1ms (EPIC-32 Risk Assessment)
- **Actual:** O(1) 纯计算 — py-fsrs 固定参数矩阵运算
- **Evidence:** `backend/app/services/review_service.py:699-763` — `FSRSManager.review_card()` + `get_due_date()`
- **Findings:** FSRS 算法为 O(1) 常数时间，单次计算远低于 1ms。无循环、无嵌套查找。

### Throughput

- **Status:** PASS ✅
- **Threshold:** 10 并发请求无异常
- **Actual:** 10 并发 `asyncio.create_task` 全部成功，JSON 文件完整性维持
- **Evidence:** `backend/tests/unit/test_card_state_concurrent_write.py:89-147` — 3 个并发测试
- **Findings:** `asyncio.Lock` (review_service.py:101) 串行化写操作，原子写入 (temp + rename) 保护数据完整性。

### Resource Usage

- **CPU Usage**
  - **Status:** PASS ✅
  - **Threshold:** FSRS 计算不增加显著 CPU 负载
  - **Actual:** O(1) 矩阵运算，单次调用微秒级
  - **Evidence:** py-fsrs 库 — 固定维度参数矩阵

- **Memory Usage**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** Card states 文件大小合理
  - **Actual:** JSON 文件随 concept 数量线性增长，无上限
  - **Evidence:** `review_service.py:98` — `fsrs_card_states.json` 单文件存储；`review_service.py:298-311` — `_save_card_states()` 写入完整 JSON

### Scalability

- **Status:** CONCERNS ⚠️
- **Threshold:** 支持 1000+ concept 不降级
- **Actual:** 当前 JSON 文件存储无分片策略，预计 1000+ concept 时文件 > 100KB
- **Evidence:** `review_service.py:98` — 单文件存储模式
- **Findings:** 当前规模 (< 200 concept) 完全可接受。建议 concept > 1000 时迁移到 SQLite。

---

## Security Assessment

### Authentication Strength

- **Status:** N/A
- **Threshold:** N/A（本地应用，无用户认证系统）
- **Actual:** 本地单用户 Obsidian 插件 + 本地 FastAPI 后端（localhost 运行）
- **Evidence:** 项目架构 — 无 OAuth/JWT/Session 管理
- **Findings:** 作为本地桌面应用，无需用户认证。API 仅在 localhost 运行。

### Authorization Controls

- **Status:** N/A
- **Threshold:** N/A
- **Actual:** 无 RBAC 需求（单用户本地应用）
- **Evidence:** 项目架构

### Data Protection

- **Status:** PASS ✅
- **Threshold:** 无 PII 泄露，数据序列化安全
- **Actual:** `json.dumps` 标准序列化，concept_id 为内存 dict key
- **Evidence:** `review_service.py:298-311` — JSON 序列化无字符串拼接；`review_service.py:98` — 固定路径构造（无用户输入参与路径）
- **Findings:** 无路径遍历风险，无 JSON 注入风险。学习数据存储在本地文件中。

### Vulnerability Management

- **Status:** PASS ✅
- **Threshold:** 0 critical 漏洞
- **Actual:** 输入验证完整 — rating clamped 1-4, score clamped 0-100, null → 安全默认值
- **Evidence:**
  - `review_service.py:825-831` — rating 类型验证 + clamping
  - `review_service.py:807-823` — score→rating 边界转换
  - `test_review_service_fsrs.py` + `test_fsrs_manager.py:370-392` — 12 个参数化边界值测试
- **Findings:** 所有用户输入均有验证和安全默认值。无 SQL（使用 JSON 文件）。

### Compliance (if applicable)

- **Status:** N/A
- **Standards:** 无适用合规标准（本地个人学习工具）
- **Actual:** 不适用
- **Evidence:** 项目范围 — 非商业/非医疗/非金融应用

---

## Reliability Assessment

### Availability (Uptime)

- **Status:** PASS ✅
- **Threshold:** 本地服务可用
- **Actual:** FastAPI 后端本地运行，Obsidian 插件本地加载
- **Evidence:** `backend/app/api/v1/endpoints/health.py:104-115` — health endpoint 正常报告 FSRS 组件状态
- **Findings:** 本地应用无云端可用性需求。Health endpoint 正确报告 FSRS 组件状态（ok/degraded）。

### Error Rate

- **Status:** PASS ✅
- **Threshold:** 0% FSRS 计算错误暴露给用户
- **Actual:** FSRS 计算失败时自动降级到 Ebbinghaus，不返回错误
- **Evidence:** `review_service.py:744-750` — try/except + Ebbinghaus fallback；响应包含 `"algorithm": "ebbinghaus-fallback"` 标识
- **Findings:** 零错误暴露给用户。所有 FSRS 失败通过 Ebbinghaus 回退透明处理。

### MTTR (Mean Time To Recovery)

- **Status:** PASS ✅
- **Threshold:** < 1 分钟
- **Actual:** `USE_FSRS=false` 环境变量即时切换回 Ebbinghaus
- **Evidence:** `review_service.py:197` — USE_FSRS 配置检查
- **Findings:** 回滚到 Ebbinghaus 只需设置环境变量并重启服务，< 30 秒。

### Fault Tolerance

- **Status:** PASS ✅
- **Threshold:** FSRS 不可用时服务正常运行
- **Actual:** 完整三层降级链
- **Evidence:**
  - Layer 1: `review_service.py:76-90` — py-fsrs ImportError → `FSRS_AVAILABLE=False`
  - Layer 2: `review_service.py:177-212` — `create_fsrs_manager()` 返回 None → 无 FSRSManager
  - Layer 3: `review_service.py:744-750` — 运行时 FSRS 异常 → Ebbinghaus fallback
  - 验证: `test_review_fsrs_degradation.py` — 5 个 E2E 降级测试
- **Findings:** 每层降级都有 WARNING 级日志记录，health endpoint 报告 degraded 状态。

### CI Burn-In (Stability)

- **Status:** CONCERNS ⚠️
- **Threshold:** 连续通过无 flaky，测试隔离可靠
- **Actual:** 152 passed, 0 failed（核心文件），但测试隔离维度 24/100 (Grade F)
- **Evidence:**
  - 对抗性审核 (2026-02-10): 152 passed, 0 failed
  - 5维度测试审核 (2026-02-10): 隔离维度 24/100 — module-scoped fixture + pytestmark scope ambiguity
  - `conftest.py:282-299` — `scope="module"` 客户端 fixture
  - `conftest.py:232-243` — `isolate_dependency_overrides()` autouse 补偿
- **Findings:** 测试当前通过但隔离架构存在结构性风险。`isolate_dependency_overrides()` autouse fixture 补偿了 module-scoped 客户端的状态泄漏，但在 CI 并行执行或随机排序下可能产生 flaky 失败。Story 32.10 已修复 datetime.now() 和 fixture cleanup 问题，但 module-scope 根因未解决。

### Disaster Recovery (if applicable)

- **RTO (Recovery Time Objective)**
  - **Status:** PASS ✅
  - **Threshold:** < 5 分钟
  - **Actual:** USE_FSRS=false 切换 < 30 秒，SQLite 数据保留
  - **Evidence:** EPIC-32 回滚计划

- **RPO (Recovery Point Objective)**
  - **Status:** PASS ✅
  - **Threshold:** 0 数据丢失
  - **Actual:** FSRS 数据存储在独立 JSON 文件，原 SQLite 表不受影响
  - **Evidence:** EPIC-32 兼容性要求 — "添加新表，不删除旧表"

---

## Maintainability Assessment

### Test Coverage

- **Status:** CONCERNS ⚠️
- **Threshold:** ≥ 90% AC 覆盖率
- **Actual:** 24/28 AC 覆盖 (86%) — Story 32.4 全部 4 个 AC 缺失
- **Evidence:**
  - 测试审核 (2026-02-10): AC 覆盖率 86%, Story 32.4 0% 覆盖
  - 缺失: AC-32.4.1 (reviewCount), AC-32.4.2 (streakDays), AC-32.4.3 (持久化), AC-32.4.4 (趋势)
  - 无 `test_dashboard_statistics.py` 或类似文件存在
- **Findings:** 核心 FSRS 路径测试完整 (32.1-32.3, 32.10-32.11)。Story 32.4 Dashboard Statistics 是唯一覆盖缺口。

### Code Quality

- **Status:** PASS ✅
- **Threshold:** 0 TODO/FIXME/HACK/STUB
- **Actual:** `grep -rn "TODO\|FIXME\|HACK\|STUB" review_service.py` → 0 匹配
- **Evidence:** 对抗性审核 (2026-02-10) — clean
- **Findings:** 代码无技术债务标记。迁移文档存在于模块 docstring 中。

### Technical Debt

- **Status:** PASS ✅
- **Threshold:** 0 死代码/DI 断裂/幻觉
- **Actual:** 0 死代码, 0 DI 断裂, 0 幻觉
- **Evidence:** 对抗性审核 (2026-02-10) — 全部代码现实检查通过
  - DI: `create_fsrs_manager(settings)` 在 `dependencies.py` 中正确传参
  - 无静态模板方法被错误调用
- **Findings:** 所有 EPIC 声称的功能在代码中均有真实实现。DI 参数 1:1 匹配。

### Documentation Completeness

- **Status:** PASS ✅
- **Threshold:** 关键方法有 docstring + AC 追踪
- **Actual:** 模块级迁移文档 + 方法级 AC 标注 + 完整 EPIC 文档
- **Evidence:** `review_service.py:1-60` (模块 doc) + `review_service.py:673-695` (AC 追踪注释)
- **Findings:** 测试可追溯性优秀 — 每个测试标注对应 AC 编号。

### Test Quality (from test-review)

- **Status:** CONCERNS ⚠️
- **Threshold:** 5维度评分 ≥ 70/100
- **Actual:** **61/100 (D)** — 5维度加权评估
- **Evidence:** `_bmad-output/test-artifacts/test-review-epic32-20260210.md`
  - Determinism: 66/100 (C+) — datetime.now() 4 处未修复
  - **Isolation: 24/100 (F)** — module-scoped fixture 泄漏状态
  - Maintainability: 72/100 (C+) — 1233行文件, 重复 fixture
  - Coverage: 78/100 (B+) — Story 32.4 缺失
  - Performance: 82/100 (A) — 零硬等待, 100% mock 驱动
- **Findings:** 隔离维度是关键瓶颈。`conftest.py:282` 的 `scope="module"` 客户端在测试间共享 `app.dependency_overrides` 可变状态。虽然 `isolate_dependency_overrides()` autouse fixture 提供了补偿，但这是治标不治本的方案。

---

## Custom NFR Assessments

### Observability (可观测性)

- **Status:** PASS ✅
- **Threshold:** 降级时有日志 + 健康检查可报告 FSRS 状态
- **Actual:** WARNING 级降级日志 + `algorithm` 字段 + `components.fsrs` 健康状态 + `_auto_persist_failures` 计数器
- **Evidence:**
  - `review_service.py:744-750` — WARNING 日志
  - `review_service.py:82-90` — FSRS_RUNTIME_OK 标志
  - `health.py:104-115` — health endpoint FSRS 组件
  - `health.py:138-189` — Prometheus 指标暴露
- **Findings:** 可观测性完整 — 日志、健康检查、指标三层覆盖。

### Infrastructure AC Compliance (基础设施验收标准)

- **Status:** PASS ✅
- **Threshold:** D1-D6 全部满足
- **Actual:** 6/6 维度通过
- **Evidence:**
  - D1 持久化: `asyncio.Lock` + atomic write (temp+rename) → JSON 文件
  - D2 弹性: FSRS→Ebbinghaus fallback + auto card creation
  - D3 输入验证: Rating 1-4 + Score 0-100 + Null → default
  - D4 配置: `USE_FSRS` 默认 True + `DESIRED_RETENTION` 默认 0.9
  - D5 降级: WARNING log + health degraded + algorithm 字段
  - D6 集成: 5 个 E2E HTTP 降级测试 + 3 个并发安全测试
- **Findings:** 完全符合基础设施 AC 检查清单。

---

## Quick Wins

3 quick wins identified for immediate implementation:

1. **pytestmark scope 明确化** (Maintainability) - LOW - 30分钟
   - 在 `test_review_service_fsrs.py:35-37` 中移除冗余 pytestmark 或设置显式 `loop_scope="function"`
   - Minimal code change, 消除 event loop scope 歧义

2. **Card states 文件大小监控** (Performance) - LOW - 1小时
   - 在 `_save_card_states()` 中添加文件大小检查，> 1MB 时 WARNING
   - No code changes needed to core logic

3. **Magic strings 替换为常量** (Maintainability) - LOW - 2小时
   - Concept IDs 和 API 路径定义为共享常量
   - Minimal code changes

---

## Recommended Actions

### Immediate (Before Release) - CRITICAL/HIGH Priority

1. **修复 module-scoped 测试 fixture** - HIGH - 2小时 - Dev
   - 将 `conftest.py:282` 的 `scope="module"` 改为 `scope="function"`
   - 或在 import time 捕获 clean state（Option B）
   - 验证: 全部 EPIC-32 测试在随机排序下通过

2. **补充 Story 32.4 测试覆盖** - HIGH - 3小时 - Dev
   - 创建 `backend/tests/unit/test_dashboard_statistics.py`
   - 覆盖: AC-32.4.1 (reviewCount), AC-32.4.2 (streakDays), AC-32.4.3 (持久化), AC-32.4.4 (趋势)
   - 验证: 28/28 AC 覆盖率

### Short-term (Next Sprint) - MEDIUM Priority

1. **datetime.now() 修复** - MEDIUM - 1小时 - Dev
   - 在 `test_review_service_fsrs.py:403-449` 应用 bracket 模式
   - 已有参考实现: `test_fsrs_manager.py:116-130`

2. **FSRS 计算 benchmark** - MEDIUM - 2小时 - Dev
   - 创建 `test_fsrs_benchmark.py`
   - 100 次 `review_card()` 调用，验证 p95 < 10ms

3. **拆分 test_review_history_pagination.py** - MEDIUM - 2小时 - Dev
   - 1233 行文件拆分为 3-4 个聚焦文件
   - 每个文件 < 300 行

### Long-term (Backlog) - LOW Priority

1. **Card states SQLite 迁移** - LOW - 8小时 - Dev
   - 当 concept > 1000 时，从 JSON 迁移到 SQLite
   - 需要迁移脚本 + 向后兼容层

2. **去重跨文件 fixture** - LOW - 2小时 - Dev
   - `override_settings` 等 fixture 在 4 个文件中重复
   - 提取到 `conftest.py` 或 `fixtures/` 模块

---

## Monitoring Hooks

5 monitoring hooks:

### Performance Monitoring

- [x] asyncio.Lock 并发保护 — 已实现 (`review_service.py:101`)
- [ ] Card states JSON 文件大小告警 — > 1MB 时 WARNING
  - **Owner:** Dev
  - **Deadline:** Next Sprint

### Security Monitoring

- [x] 输入验证 (rating/score clamping) — 已实现 (`review_service.py:825-831`)

### Reliability Monitoring

- [x] Health endpoint FSRS 组件状态 (`components.fsrs`) — 已实现 (`health.py:104-115`)
- [x] FSRS_RUNTIME_OK 标志 + health endpoint — 已实现

### Alerting Thresholds

- [x] 三层降级自动告警 (WARNING 日志) — 已实现
- [ ] 测试稳定性监控 — 随机排序 CI run 检测 flaky
  - **Owner:** Dev
  - **Deadline:** Next Sprint

---

## Fail-Fast Mechanisms

4 fail-fast mechanisms — all core already implemented:

### Circuit Breakers (Reliability)

- [x] FSRS → Ebbinghaus 三层降级路径
  - **Evidence:** `review_service.py:76-90, 177-212, 744-750`

### Rate Limiting (Performance)

- [x] asyncio.Lock 串行化 card state 写入
  - **Evidence:** `review_service.py:101, 304`

### Validation Gates (Security)

- [x] Rating clamped 1-4, Score clamped 0-100, Invalid → default
  - **Evidence:** `review_service.py:807-831`

### Smoke Tests (Maintainability)

- [x] 152 核心测试 + 5 E2E 降级 + 3 并发安全
  - **Evidence:** 对抗性审核 2026-02-10

---

## Evidence Gaps

3 evidence gaps identified:

- [ ] **FSRS 计算 Benchmark** (Performance)
  - **Owner:** Dev
  - **Deadline:** Next Sprint
  - **Suggested Evidence:** pytest-benchmark — p95/p99 延迟测量
  - **Impact:** LOW — 算法已知 O(1)，但缺少正式测量数据

- [ ] **Card States 文件增长监控** (Scalability)
  - **Owner:** Dev
  - **Deadline:** Next Sprint
  - **Suggested Evidence:** 文件大小 + concept 数量相关性测试
  - **Impact:** LOW — 当前规模完全可接受

- [ ] **Story 32.4 Dashboard Statistics 测试** (Coverage)
  - **Owner:** Dev
  - **Deadline:** Before Release
  - **Suggested Evidence:** `test_dashboard_statistics.py` — 4 AC 验证
  - **Impact:** HIGH — 4 个 AC 完全无测试覆盖

---

## Findings Summary

**Based on ADR Quality Readiness Checklist (8 categories, 29 criteria)**

| Category                                         | Criteria Met | PASS | CONCERNS | FAIL | Overall Status     |
| ------------------------------------------------ | ------------ | ---- | -------- | ---- | ------------------ |
| 1. Testability & Automation                      | 3/4          | 3    | 1        | 0    | CONCERNS ⚠️        |
| 2. Test Data Strategy                            | 3/3          | 3    | 0        | 0    | PASS ✅             |
| 3. Scalability & Availability                    | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️        |
| 4. Disaster Recovery                             | 3/3          | 3    | 0        | 0    | PASS ✅             |
| 5. Security                                      | 4/4          | 4    | 0        | 0    | PASS ✅             |
| 6. Monitorability, Debuggability & Manageability | 4/4          | 4    | 0        | 0    | PASS ✅             |
| 7. QoS & QoE                                     | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️        |
| 8. Deployability                                 | 3/3          | 3    | 0        | 0    | PASS ✅             |
| **Total**                                        | **24/29**    | **24** | **5**  | **0** | **CONCERNS ⚠️**   |

**Criteria Met Scoring:**

- 24/29 (83%) = Room for improvement (20-25 range)
- 降级原因: Testability 1.1 (Isolation) 从 PASS 降为 CONCERNS

**与上次评估对比 (2026-02-10):**

| 指标 | 上次 (v1) | 本次 (v2) | 变化 |
|------|----------|----------|------|
| 总分 | 25/29 (86%) | 24/29 (83%) | -1 |
| 测试审核评分 | 91/100 (A-) | 61/100 (D) | **-30** |
| Testability | 4/4 PASS | 3/4 CONCERNS | -1 |
| CI Burn-In | PASS | CONCERNS | 降级 |
| Test Coverage | PASS (95%) | CONCERNS (86%) | 降级 |
| 评估方法 | 手动+对抗性 | 5维度加权+对抗性 | 更严格 |

---

## Gate YAML Snippet

```yaml
nfr_assessment:
  date: '2026-02-11'
  story_id: 'EPIC-32'
  feature_name: 'Ebbinghaus Review System Enhancement (FSRS-4.5 Integration)'
  adr_checklist_score: '24/29'
  categories:
    testability_automation: 'CONCERNS'
    test_data_strategy: 'PASS'
    scalability_availability: 'CONCERNS'
    disaster_recovery: 'PASS'
    security: 'PASS'
    monitorability: 'PASS'
    qos_qoe: 'CONCERNS'
    deployability: 'PASS'
  overall_status: 'CONCERNS'
  critical_issues: 0
  high_priority_issues: 2
  medium_priority_issues: 3
  concerns: 5
  blockers: false
  quick_wins: 3
  evidence_gaps: 3
  recommendations:
    - '修复 conftest.py module-scoped fixture 隔离问题 (HIGH)'
    - '补充 Story 32.4 Dashboard Statistics 测试覆盖 (HIGH)'
    - '修复 datetime.now() midnight boundary 模式 (MEDIUM)'
    - '添加 FSRS 计算 benchmark (MEDIUM)'
    - '规划 concept > 1000 时的 SQLite 迁移方案 (LOW)'
```

---

## Related Artifacts

- **EPIC File:** `docs/epics/EPIC-32-EBBINGHAUS-REVIEW-SYSTEM-ENHANCEMENT.md`
- **Test Review (5维度):** `_bmad-output/test-artifacts/test-review-epic32-20260210.md` (61/100, D)
- **Test Review (初版):** `_bmad-output/test-artifacts/test-review-epic32-20260209.md`
- **Adversarial Review:** `_bmad-output/test-artifacts/test-review-epic32-adversarial-20260210.md`
- **Traceability Matrix:** `_bmad-output/test-artifacts/traceability-matrix-epic32.md`
- **Trace Coverage Matrix:** `_bmad-output/test-artifacts/tea-trace-coverage-matrix-epic32.json`
- **Evidence Sources:**
  - Test Results: `backend/tests/unit/test_fsrs_*.py`, `backend/tests/unit/test_review_service_fsrs.py`, `backend/tests/unit/test_card_state_concurrent_write.py`, `backend/tests/e2e/test_review_fsrs_degradation.py`
  - Source Code: `backend/app/services/review_service.py`, `backend/app/api/v1/endpoints/review.py`, `backend/app/api/v1/endpoints/health.py`
  - Configuration: `backend/app/dependencies.py`, `backend/app/core/config.py`
  - Plugin: `canvas-progress-tracker/obsidian-plugin/src/services/PriorityCalculatorService.ts`

---

## Recommendations Summary

**Release Blocker:** 无（0 FAIL）

**High Priority:** 2 个测试质量问题
1. Module-scoped fixture 隔离 → 需修复后才能确保 CI 稳定性
2. Story 32.4 零覆盖 → 需补充测试确保 Dashboard 功能可验证

**Medium Priority:** 3 个优化建议（datetime 修复 + benchmark + 文件拆分）

**Next Steps:**
- 修复 2 个 HIGH 问题后，重新运行 `*nfr-assess` 预期可升级为 PASS
- CONCERNS 为非阻塞性但影响长期可维护性

---

## Sign-Off

**NFR Assessment:**

- Overall Status: CONCERNS ⚠️
- Critical Issues: 0
- High Priority Issues: 2
- Concerns: 5
- Evidence Gaps: 3

**Gate Status:** CONCERNS ⚠️ (有条件通过 — 无阻塞级 FAIL，但 HIGH 问题影响测试可靠性)

**Next Actions:**

- If PASS ✅: Proceed to `*gate` workflow or release
- If CONCERNS ⚠️: Address HIGH/CRITICAL issues, re-run `*nfr-assess` ← **当前状态**
- If FAIL ❌: Resolve FAIL status NFRs, re-run `*nfr-assess`

**Generated:** 2026-02-11
**Workflow:** testarch-nfr v5.0 (ADR Quality Readiness Checklist)
**Assessor:** Claude Opus 4.6 (parallel 4-domain assessment)
**Test Review Score:** 61/100 (D) — 5维度加权评估
**ADR Checklist Score:** 24/29 (83%)
**Previous Assessment:** 2026-02-10 — 25/29 (86%), PASS

---

<!-- Powered by BMAD-CORE™ -->
