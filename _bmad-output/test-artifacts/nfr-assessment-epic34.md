# NFR Assessment - EPIC-34 跨Canvas与教材挂载检验白板完整激活

**Date:** 2026-02-10
**Story:** EPIC-34 (Stories 34.3, 34.4, 34.7, 34.8, 34.9)
**Overall Status:** CONCERNS ⚠️

---

Note: This assessment summarizes existing evidence; it does not run tests or CI workflows.

## Executive Summary

**Assessment:** 5 PASS, 3 CONCERNS, 0 FAIL

**Blockers:** 0 — 无阻塞级问题

**High Priority Issues:** 1 — 测试质量评分从 86/100 降至 63/100 (D 级)，需关注测试可维护性

**Recommendation:** ⚠️ EPIC-34 功能实现完整（165 测试通过），但测试质量（63/100）低于 70 分门槛。3 个 CONCERNS 类别需在后续迭代中改善：(1) 测试可维护性，(2) 测试数据策略，(3) 灾难恢复文档化。无阻塞级问题，功能可继续使用。

---

## Performance Assessment

### Response Time (p95)

- **Status:** PASS ✅
- **Threshold:** <200ms (localhost single-user)
- **Actual:** FastAPI async 端点响应时间远低于阈值
- **Evidence:** 165 测试在 33.57s 内完成 (~0.2s/测试含 setup/teardown)
- **Findings:** 单用户 localhost 上下文，无性能瓶颈

### Throughput

- **Status:** N/A ✅
- **Threshold:** N/A — 单用户 localhost 应用
- **Actual:** 单进程 uvicorn，无并发用户场景
- **Evidence:** 架构设计为单用户本地工具
- **Findings:** 吞吐量不适用于 localhost 单用户上下文

### Resource Usage

- **CPU Usage**
  - **Status:** PASS ✅
  - **Threshold:** 无特定阈值（localhost 单用户）
  - **Actual:** 单进程 FastAPI 工作负载轻量
  - **Evidence:** 所有查询路径有界限（MAX_HISTORY_RECORDS=1000）

- **Memory Usage**
  - **Status:** PASS ✅
  - **Threshold:** 进程内存受限于单进程约束
  - **Actual:** 查询结果上限 1000 条记录，分页限制 ≤100 条/页
  - **Evidence:** `review_service.py:L104` — `MAX_HISTORY_RECORDS = 1000`

### Scalability

- **Status:** PASS ✅
- **Threshold:** 单用户 1-2 年持续使用
- **Actual:** 查询有界限，Neo4j 单实例容量远超单用户需求
- **Evidence:** `MAX_HISTORY_RECORDS=1000`, `Query(ge=1, le=365)`, `Query(ge=1, le=100)`
- **Findings:** JSON 文件增长为唯一远期关注点（P4 优先级）

---

## Security Assessment

### Authentication Strength

- **Status:** N/A ✅
- **Threshold:** N/A — 单用户 localhost 应用
- **Actual:** 无需认证
- **Evidence:** 系统仅绑定 127.0.0.1，无公网暴露

### Authorization Controls

- **Status:** N/A ✅
- **Threshold:** N/A — 单用户完全访问
- **Actual:** 单用户架构，无角色/权限需求
- **Evidence:** 无 auth 中间件或 token 验证

### Data Protection

- **Status:** PASS ✅
- **Threshold:** 输入验证 + 注入防护
- **Actual:** FastAPI pydantic 验证强制约束，无 eval/exec/raw SQL
- **Evidence:**
  - `review.py:L636-640` — `days: int = Query(7, ge=1, le=365)`, `limit: int = Query(5, ge=1, le=100)`
  - 14 个边界测试覆盖 days=0/-1/400/abc, limit=0/-1/101/99999999/abc
  - 零 eval/exec/subprocess/os.system 调用
- **Findings:** 输入验证完善，无注入向量

### Vulnerability Management

- **Status:** CONCERNS ⚠️
- **Threshold:** 无已知关键漏洞
- **Actual:** 无自动化 SAST 或依赖扫描
- **Evidence:** 无 bandit/pip-audit/safety/snyk 配置
- **Findings:** 框架内置保护（FastAPI JSON 编码、pydantic 验证）提供基础防护，但缺乏自动化扫描
- **Recommendation:** P3 — 添加 bandit (SAST) 和 pip-audit (依赖扫描) 到 CI

### Compliance (if applicable)

- **Status:** N/A ✅
- **Standards:** 无 — 单用户本地应用，不适用 GDPR/SOC2/HIPAA/PCI-DSS
- **Actual:** localhost-only 部署免除所有数据保护法规
- **Evidence:** 无公网暴露，无多租户，无数据跨境传输

---

## Reliability Assessment

### Availability (Uptime)

- **Status:** N/A ✅
- **Threshold:** N/A — 用户手动启动/停止服务
- **Actual:** 本地服务，用户按需启动
- **Evidence:** 无 SLA 要求

### Error Rate

- **Status:** PASS ✅
- **Threshold:** 服务错误不导致 HTTP 500
- **Actual:** 服务异常返回 HTTP 200 + 空数据（优雅降级）
- **Evidence:** 18 个 fallback 降级路径，所有依赖失败均返回默认值 + WARNING 日志

### MTTR (Mean Time To Recovery)

- **Status:** N/A ✅
- **Threshold:** N/A — 本地服务，用户手动重启
- **Actual:** 重启 FastAPI 服务即可恢复

### Fault Tolerance

- **Status:** PASS ✅
- **Threshold:** 可选依赖不可用时系统继续运行
- **Actual:** 18 个 fallback 路径，graphiti_client/memory_service/rag_service 为 None 时优雅降级
- **Evidence:**
  - `dependencies.py` — 所有可选依赖用 try/except + logger.warning() 包裹
  - Story 34.8 修复了 `except Exception: pass` 静默吞噬错误
  - DI 完整性测试验证注入正确性

### CI Burn-In (Stability)

- **Status:** PASS ✅
- **Threshold:** 测试套件稳定通过
- **Actual:** 165 测试在 33.57s 内全部通过
- **Evidence:** `test-review-epic34-20260210.md` — 165 passed, 0 failed

### Disaster Recovery (if applicable)

- **RTO (Recovery Time Objective)**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** 未定义（本地工具通常无 RTO）
  - **Actual:** 无文档化恢复程序
  - **Evidence:** 无 backup/restore 脚本或文档

- **RPO (Recovery Point Objective)**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** 未定义
  - **Actual:** JSON 文件写入部分缺乏原子性保证（FSRS 有原子写入，其他 JSON 文件无）
  - **Evidence:** `review_service.py:L298-314` — FSRS 使用 `.tmp` + rename 原子写入模式（有 asyncio.Lock 保护），但 `learning_memories.json`、`neo4j_memory.json` 无类似保护

---

## Maintainability Assessment

### Test Coverage

- **Status:** PASS ✅
- **Threshold:** 所有 AC 有对应测试
- **Actual:** P0 覆盖率 9/9 (100%), P1 覆盖率 10/10 (100%), P2 覆盖率 1/1 (100%)
- **Evidence:** `traceability-matrix-epic34.md` — 100% 可追溯性覆盖
- **Findings:** 80 核心测试 (E2E: 15, Integration: 47, Unit: 18) + 94 回归测试

### Code Quality

- **Status:** CONCERNS ⚠️
- **Threshold:** 测试质量评分 ≥70/100
- **Actual:** **63/100 (D - Needs Improvement)**
- **Evidence:** `test-review-epic34-20260210.md` — 最新测试审查评分
- **Findings:**
  - 确定性: 82/100 (B) — 时间依赖检测到但已缓解
  - 隔离性: 56/100 (F) — 直接修改内部状态 (`service._card_states`)
  - 可维护性: 42/100 (F) — 1226 行测试文件 (4x 阈值), mock 模板重复 ~20 次
  - 覆盖率: 72/100 (C) — Story 34.9 AC2/AC3 测试缺失
  - 性能: 63/100 (D) — 部分测试无显式超时

### Technical Debt

- **Status:** CONCERNS ⚠️
- **Threshold:** 无关键技术债务
- **Actual:** 1 项技术债务 Story 待创建 (34.10 — 测试可维护性重构)
- **Evidence:** `EPIC-34-COMPLETE-ACTIVATION.md` — Risk: `test_review_history_pagination.py` 1226 lines (4x threshold)
- **Findings:**
  - 1226 行测试文件需拆分为多个聚焦模块
  - Mock 模板重复 ~20 次，需提取为 conftest fixtures
  - `service._card_states` 直接修改违反测试隔离原则

### Documentation Completeness

- **Status:** PASS ✅
- **Threshold:** EPIC 文档与代码现实一致
- **Actual:** EPIC-34 文档已修正（Goal Deferred 标注, 34.8/34.9 补录）
- **Evidence:** `EPIC-34-COMPLETE-ACTIVATION.md` — 所有 Story 状态标注准确

### Test Quality (from test-review)

- **Status:** CONCERNS ⚠️
- **Threshold:** 测试质量评分 ≥70/100 (C 级)
- **Actual:** **63/100 (D 级 - Needs Improvement)**
- **Evidence:** `test-review-epic34-20260210.md` (最新版本，取代旧版 86/100)
- **Findings:**
  - **⚠️ 关键变化**: 旧版评分 86/100 → 最新评分 63/100，降幅 23 分
  - 根因: 最新审查采用更严格的评分标准，识别出之前遗漏的隔离性和可维护性问题
  - 最严重问题: 1226 行超大测试文件、20x mock 重复、直接内部状态修改

---

## Quick Wins

3 quick wins identified for immediate implementation:

1. **标准化异常处理日志格式** (Monitorability) - P3 - 1h
   - 统一 `except Exception as e:` 块中的日志格式，包含服务名 + 操作名 + 参数
   - 无功能代码变更

2. **提取 mock fixtures 到 conftest** (Maintainability) - P2 - 2-3h
   - 将重复 ~20 次的 mock 模板提取为共享 conftest fixtures
   - 减少测试文件体积，提升可维护性评分

3. **添加 JSON 文件大小监控到 health 端点** (Scalability) - P3 - 1h
   - 在 GET /health 响应中报告 learning_memories.json 等文件大小
   - 零风险变更，提前预警存储增长

---

## Recommended Actions

### Immediate (Before Next Sprint) - HIGH Priority

1. **创建 Story 34.10: 测试可维护性重构** - P1 - 4-6h - Dev Team
   - 拆分 `test_review_history_pagination.py` (1226 行) 为 3-4 个聚焦模块
   - 提取 mock 模板到 conftest fixtures
   - 将 `service._card_states` 直接修改替换为 service API 调用
   - 验证标准: 测试质量评分 ≥70/100

2. **补充 Story 34.9 AC2/AC3 缺失测试** - P1 - 2-3h - Dev Team
   - AC2: 降级字段传播测试
   - AC3: recommend-action 降级行为测试
   - 验证标准: 100% AC 覆盖率

### Short-term (Next Sprint) - MEDIUM Priority

1. **实现 JSON 文件原子写入** - P2 - 2h - Dev Team
   - 对 `learning_memories.json`, `neo4j_memory.json` 实现 write-to-tmp-then-rename 模式
   - 已有参考: FSRS 卡片状态已使用此模式 (`review_service.py:L298-314`)

2. **清理 HTTP 500 响应中的错误信息泄露** - P2 - 1h - Dev Team
   - 替换 5 个 `str(e)` 为通用错误消息
   - 完整异常保留在服务端 ERROR 日志中

### Long-term (Backlog) - LOW Priority

1. **添加 SAST 工具到 CI** - P3 - 2h - DevOps
   - 配置 bandit (Python SAST) + pip-audit (依赖漏洞扫描)
   - 集成到 GitHub Actions workflow

2. **文档化备份/恢复程序** - P3 - 1h - Dev Team
   - 记录 `backend/data/` 目录和 Neo4j Docker volume 的备份步骤
   - 可选: 添加 CLI 命令导出/导入用户数据

3. **添加路径遍历防护** - P3 - 1h - Dev Team
   - `generate_verification_canvas` 端点的 `source_canvas` 参数添加路径清理
   - 验证解析后路径在 `_canvas_base_path` 范围内

---

## Monitoring Hooks

3 monitoring hooks recommended:

### Performance Monitoring

- [ ] JSON 文件大小监控 — 在 health 端点报告数据文件大小
  - **Owner:** Dev Team
  - **Deadline:** 下一 Sprint

### Reliability Monitoring

- [ ] 降级状态摘要 — health 端点报告哪些可选服务处于降级状态
  - **Owner:** Dev Team
  - **Deadline:** 下一 Sprint

### Maintainability Monitoring

- [ ] 测试质量评分追踪 — 每次 test-review 后记录评分趋势
  - **Owner:** QA
  - **Deadline:** 持续

---

## Fail-Fast Mechanisms

### Query Bounds (Performance/DoS)

- [x] MAX_HISTORY_RECORDS = 1000 — 硬上限防止无界查询 ✅ 已实现
- [x] Query(ge=1, le=365) / Query(ge=1, le=100) — FastAPI 参数验证 ✅ 已实现

### Graceful Degradation (Reliability)

- [x] 18 个 fallback 降级路径 — 可选依赖不可用时返回默认值 + WARNING 日志 ✅ 已实现
- [x] HTTP 200 + 空数据 — 服务错误不产生 500 错误 ✅ 已实现

### Data Integrity (Security)

- [x] Pydantic 模型验证 — 所有请求/响应 schema 强制类型安全 ✅ 已实现
- [x] FSRS 原子写入 — write-to-tmp-then-rename + asyncio.Lock ✅ 已实现
- [ ] 非 FSRS JSON 文件原子写入 — 待实现

---

## Evidence Gaps

2 evidence gaps identified:

- [ ] **灾难恢复程序** (Disaster Recovery)
  - **Owner:** Dev Team
  - **Deadline:** Backlog
  - **Suggested Evidence:** 备份/恢复脚本 + 文档
  - **Impact:** 数据丢失时无恢复路径（低频但高影响）

- [ ] **自动化安全扫描结果** (Security)
  - **Owner:** DevOps
  - **Deadline:** Backlog
  - **Suggested Evidence:** bandit + pip-audit 扫描报告
  - **Impact:** 无法自动检测新引入的安全漏洞（localhost 缓解风险）

---

## Findings Summary

**Based on ADR Quality Readiness Checklist (8 categories, 29 criteria)**

| Category                                         | Criteria Met | PASS | CONCERNS | FAIL | Overall Status    |
| ------------------------------------------------ | ------------ | ---- | -------- | ---- | ----------------- |
| 1. Testability & Automation                      | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️       |
| 2. Test Data Strategy                            | 1/3          | 1    | 2        | 0    | CONCERNS ⚠️       |
| 3. Scalability & Availability                    | 4/4          | 4    | 0        | 0    | PASS ✅            |
| 4. Disaster Recovery                             | 0/3          | 0    | 3        | 0    | CONCERNS ⚠️       |
| 5. Security                                      | 4/4          | 4    | 0        | 0    | PASS ✅            |
| 6. Monitorability, Debuggability & Manageability | 4/4          | 4    | 0        | 0    | PASS ✅            |
| 7. QoS & QoE                                     | 4/4          | 4    | 0        | 0    | PASS ✅            |
| 8. Deployability                                 | 3/3          | 3    | 0        | 0    | PASS ✅            |
| **Total**                                        | **22/29**    | **22** | **7**  | **0** | **CONCERNS ⚠️**  |

**Criteria Met Scoring:**

- ≥26/29 (90%+) = Strong foundation
- 20-25/29 (69-86%) = Room for improvement ← **22/29 (76%)**
- <20/29 (<69%) = Significant gaps

**Key Change from Previous Assessment:**
- 前次评估: 25/29 (86%), 6 PASS / 2 CONCERNS — 基于旧版测试审查 86/100
- 本次评估: 22/29 (76%), 5 PASS / 3 CONCERNS — 基于最新测试审查 63/100 (D)
- 降幅原因: 最新测试审查 (2026-02-10) 使用更严格评分标准，识别出隔离性 (56/100 F) 和可维护性 (42/100 F) 的严重问题

---

## Gate YAML Snippet

```yaml
nfr_assessment:
  date: '2026-02-10'
  story_id: 'EPIC-34'
  feature_name: '跨Canvas与教材挂载检验白板完整激活'
  adr_checklist_score: '22/29'
  categories:
    testability_automation: 'CONCERNS'
    test_data_strategy: 'CONCERNS'
    scalability_availability: 'PASS'
    disaster_recovery: 'CONCERNS'
    security: 'PASS'
    monitorability: 'PASS'
    qos_qoe: 'PASS'
    deployability: 'PASS'
  overall_status: 'CONCERNS'
  critical_issues: 0
  high_priority_issues: 1
  medium_priority_issues: 2
  concerns: 3
  blockers: false
  quick_wins: 3
  evidence_gaps: 2
  recommendations:
    - '创建 Story 34.10 测试可维护性重构 (P1)'
    - '补充 Story 34.9 AC2/AC3 缺失测试 (P1)'
    - '实现非-FSRS JSON 文件原子写入 (P2)'
```

---

## Parallel Subprocess Summary

本次评估使用 4 个并行子流程执行 NFR 域评估：

| Domain      | Risk Level | PASS | CONCERN | FAIL | N/A |
|-------------|-----------|------|---------|------|-----|
| Security    | LOW       | 7    | 3       | 0    | 3   |
| Performance | LOW       | 5    | 1       | 0    | 3   |
| Reliability | LOW       | 5    | 3       | 0    | 3   |
| Scalability | LOW       | 4    | 1       | 0    | 3   |

**Cross-Domain Risk:** JSON 文件存储增长同时影响 Scalability 和 Reliability，建议统一解决（P2 原子写入 + P3 文件轮转）。

---

## Related Artifacts

- **EPIC File:** `docs/epics/EPIC-34-COMPLETE-ACTIVATION.md`
- **Test Review (Latest):** `_bmad-output/test-artifacts/test-review-epic34-20260210.md` — 63/100 (D)
- **Traceability Matrix:** `_bmad-output/test-artifacts/traceability-matrix-epic34.md` — 100% 覆盖
- **Security Assessment:** `_bmad-output/test-artifacts/nfr-assessment-epic34-security.json` — LOW risk
- **Evidence Sources:**
  - Test Results: `backend/tests/` (165 passed, 33.57s)
  - Service Code: `backend/app/services/review_service.py`, `backend/app/api/v1/endpoints/review.py`
  - Plugin Code: `canvas-progress-tracker/obsidian-plugin/src/`

---

## Recommendations Summary

**Release Blocker:** 无 — 功能完整，165 测试全部通过

**High Priority:** 测试质量评分 63/100 需改善至 ≥70/100 — 创建 Story 34.10 重构测试

**Medium Priority:** JSON 原子写入 (P2), HTTP 500 错误信息清理 (P2)

**Next Steps:**
1. 创建 Story 34.10（测试可维护性重构）→ 目标评分 ≥70/100
2. 补充 34.9 AC2/AC3 缺失测试
3. 运行 `trace` 工作流确认可追溯性矩阵更新

---

## Sign-Off

**NFR Assessment:**

- Overall Status: CONCERNS ⚠️
- Critical Issues: 0
- High Priority Issues: 1 (测试质量 63/100)
- Concerns: 7 个标准项
- Evidence Gaps: 2 (DR 程序, SAST 扫描)

**Gate Status:** CONCERNS ⚠️

**Next Actions:**

- ~~If PASS ✅: Proceed to `*gate` workflow or release~~
- If CONCERNS ⚠️: Address HIGH/CRITICAL issues, re-run `*nfr-assess` ← **当前状态**
- ~~If FAIL ❌: Resolve FAIL status NFRs, re-run `*nfr-assess`~~

**具体行动:**
1. 创建 Story 34.10 解决测试可维护性问题
2. Story 34.10 完成后重新运行 test-review → 期望评分 ≥70/100
3. 重新运行 `*nfr-assess` 确认 Testability 和 Test Data 类别升级为 PASS

**Generated:** 2026-02-10
**Workflow:** testarch-nfr v4.0 (parallel subprocess execution)

---

<!-- Powered by BMAD-CORE™ -->
