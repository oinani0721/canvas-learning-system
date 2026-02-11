# NFR Assessment - EPIC-35 多模态功能完整激活 (Multimodal Activation)

**Date:** 2026-02-10
**Story:** EPIC-35 (9 Stories: 35.1-35.9, 补充: 35.10-35.12)
**Overall Status:** CONCERNS ⚠️

---

Note: This assessment summarizes existing evidence; it does not run tests or CI workflows.

> **⚠️ 版本注意 (Adversarial Review 2026-02-10 补充):**
>
> 本 NFR 引用了两份 test-review，它们审查的是**不同代码状态**：
>
> | 文档 | 审查代码状态 | 分数 | 说明 |
> |------|-------------|------|------|
> | `test-review-epic35-20260209.md` | git HEAD (已提交代码) | 54/100 (F) | 审查的是 `test_multimodal_workflow.py` (934行, 含17处条件断言) |
> | `test-review-epic35-20260210.md` | working tree (未提交代码) | 82/100 (A) | 审查的是 3 个拆分后的 E2E 文件 (594行, 0条件断言) |
>
> 分数差距 (54→82) 主要因为 02-10 审查的是工作树中**已修复条件断言**的新文件，而非 git HEAD 中的旧文件。
> 两份审查均为有效评估，但针对不同代码快照。本 NFR 中引用的 54/100 分数对应的是旧 E2E 文件。
> 新 E2E 文件已于 2026-02-10 通过 `git add` 加入暂存区。

## Executive Summary

**Assessment:** 3 PASS, 5 CONCERNS, 0 FAIL

**Blockers:** 0 — 无阻塞级问题

**High Priority Issues:** 5 — 认证缺失、无负载测试、E2E 测试结构缺陷、灾难恢复未定义、无速率限制

**Recommendation:** 有条件通过 — 无阻塞级 FAIL，但 5 个 CONCERNS 需在 GA 前解决。安全认证和测试质量是最高优先级。

---

## Performance Assessment

### Response Time (p95)

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN (仅 EPIC 定义 "10 张图片 < 5 秒", 无 P95/P99 SLO)
- **Actual:** 测试使用 69 字节 PNG 文件，与生产文件大小 (50MB) 差距巨大
- **Evidence:** `backend/tests/e2e/test_multimodal_workflow.py` — `test_batch_upload_10_images_under_5_seconds`
- **Findings:** E2E 性能测试存在但使用微小测试文件，无法代表真实负载。测试使用 `if response.status_code == 201:` 条件断言 (P0 Critical from test-review)，当 API 返回错误时测试静默通过。无 pytest-benchmark 统计。

### Throughput

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN
- **Actual:** 5 并发上传测试存在 (`test_concurrent_upload_performance`)，但无大规模吞吐量测试
- **Evidence:** `backend/tests/e2e/test_multimodal_workflow.py`, `backend/tests/integration/test_multimodal_real_persistence.py`
- **Findings:** 并发上传通过 `ThreadPoolExecutor + TestClient` 实现，可能序列化请求而非真正并发。无 k6/locust 负载测试。

### Resource Usage

- **CPU Usage**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** UNKNOWN
  - **Actual:** 未测量
  - **Evidence:** 无 CPU profiling 证据

- **Memory Usage**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** UNKNOWN
  - **Actual:** 未测量；大文件上传时 `file_bytes: bytes` 参数将整个文件加载到内存
  - **Evidence:** `multimodal_service.py:505` — `upload_file(file_bytes: bytes, ...)` 接受完整字节数据

### Scalability

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN
- **Actual:** 仅 5 并发、10 文件的小规模测试；无 10K+ 项目规模测试
- **Evidence:** `test_multimodal_real_persistence.py::test_concurrent_uploads_no_data_loss` (5 并发)
- **Findings:** Singleton 模式 + 内存 `_content_store` 不支持水平扩展。LanceDB 向量搜索在大规模索引下的性能未验证。

---

## Security Assessment

### Authentication Strength

- **Status:** CONCERNS ⚠️
- **Threshold:** 所有 API 端点应有认证保护
- **Actual:** 多模态 API 端点无认证/授权机制 — 完全开放
- **Evidence:** `backend/app/api/v1/endpoints/multimodal.py` — 路由无 `Depends(get_current_user)` 或类似认证依赖
- **Findings:** 任何人可以上传、删除、查询多模态内容。这是设计决策（本地 Obsidian 插件场景），但在多用户或网络暴露场景下是安全风险。
- **Recommendation:** 对于本地使用场景可接受 (CONCERNS 而非 FAIL)；如果后端暴露到网络，必须添加 JWT/OAuth 认证层。

### Authorization Controls

- **Status:** CONCERNS ⚠️
- **Threshold:** 最小权限原则
- **Actual:** 无授权控制 — 所有用户共享所有内容
- **Evidence:** API 端点无用户/角色检查
- **Findings:** 与认证问题相同 — 本地场景可接受，网络场景需要 RBAC。

### Data Protection

- **Status:** CONCERNS ⚠️
- **Threshold:** 数据传输加密 + 静态存储保护
- **Actual:** 传输层依赖 HTTP (非 HTTPS)；文件以明文存储在 `.canvas-learning/multimodal/` 目录
- **Evidence:** `multimodal_service.py:160-170` — `DEFAULT_STORAGE_PATH = ".canvas-learning/multimodal"`
- **Findings:** 本地文件系统存储，无加密。对于个人学习工具场景可接受。

### Vulnerability Management

- **Status:** PASS ✅
- **Threshold:** 0 critical, <3 high vulnerabilities in input validation
- **Actual:** 多层输入验证机制完整
- **Evidence:**
  - **MIME 类型验证**: `multimodal_service.py:54-66` — 白名单制
  - **Magic Bytes 验证**: `multimodal_service.py:396-456` — PNG/JPEG/GIF/PDF 文件头检查
  - **文件大小限制**: `multimodal_service.py:377-381` — 默认 50MB (可配置)
  - **路径遍历防护**: `multimodal_service.py:478-503` — `_validate_safe_path()` + `resolve()` + `is_relative_to()`
  - **SSRF 防护**: `multimodal_schemas.py:90-107` — 阻止 localhost/云元数据端点
  - **测试覆盖**: `test_multimodal_path_security.py` — 3 层防御测试 (单元+集成+真实防御链)
- **Findings:** 输入验证是 EPIC-35 安全性的亮点。路径遍历防护经过分层测试验证，SSRF 保护涵盖常见攻击向量。

### Compliance (if applicable)

- **Status:** N/A
- **Standards:** 无特定合规要求 (个人学习工具)
- **Actual:** N/A
- **Evidence:** N/A
- **Findings:** 非商业产品，无 GDPR/HIPAA/PCI-DSS 合规要求

---

## Reliability Assessment

### Availability (Uptime)

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN (无 SLA 定义)
- **Actual:** Health check 端点存在并返回降级状态
- **Evidence:** `multimodal_service.py:995-1052` — `get_health_status()` 检查存储可写性、LanceDB 连接、Neo4j 连接
- **Findings:** 健康检查实现完整，但无可用性目标和监控。

### Error Rate

- **Status:** PASS ✅
- **Threshold:** 错误应有友好处理
- **Actual:** 自定义异常层次结构 + HTTP 错误映射完整
- **Evidence:**
  - 异常类: `MultimodalServiceError`, `FileValidationError`, `ContentNotFoundError` (`multimodal_service.py:119-140`)
  - HTTP 映射: 415 (不支持媒体类型), 404 (未找到), 500 (服务错误) (`endpoints/multimodal.py:138-149`)
- **Findings:** 错误处理模式一致且全面，用户不会看到原始堆栈跟踪。

### MTTR (Mean Time To Recovery)

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN
- **Actual:** JSON 持久化支持服务重启恢复 (已测试验证)
- **Evidence:** `test_multimodal_real_persistence.py::test_data_survives_service_restart` — 创建两个 Service 实例模拟重启
- **Findings:** 数据持久化保证服务重启后数据不丢失。但无自动恢复机制或 MTTR 目标。

### Fault Tolerance

- **Status:** PASS ✅
- **Threshold:** 外部依赖故障时应降级而非崩溃
- **Actual:** 完整的降级链：MultimodalStore → JSON 备用；向量搜索 → 文本搜索
- **Evidence:**
  - 双存储降级: `multimodal_service.py:180-187` — MultimodalStore 不可用时降级为 JSON
  - 搜索降级: `multimodal_service.py:1278-1351` — 向量搜索不可用时降级为文本搜索 + WARNING 日志
  - Embedding 重试: `multimodal_service.py:1353-1395` — 指数退避 (2 次重试, 2 秒延迟)
  - 前端通知: `MediaPanel.ts:385-391` — 降级时显示 "当前使用关键字搜索" 提示
  - 测试覆盖: `test_multimodal_fixes.py` — 搜索降级、日志验证、search_mode 字段验证
- **Findings:** 降级策略是 EPIC-35 可靠性的核心优势。用户可感知降级状态，日志记录透明。

### CI Burn-In (Stability)

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN
- **Actual:** 无 CI burn-in 证据；E2E 测试有结构性缺陷 (条件断言静默通过)
- **Evidence:** `test-review-epic35-20260209.md` — "8+ E2E tests silently skip assertions"
- **Findings:** 测试质量分数 54/100 (F 级)。CI 管道无法可靠检测回归，因为 E2E 测试在 API 失败时静默通过。

### Disaster Recovery (if applicable)

- **RTO (Recovery Time Objective)**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** UNKNOWN
  - **Actual:** 服务重启恢复时间未测量；JSON 持久化使恢复可能
  - **Evidence:** 数据存储在本地文件系统，重启即恢复

- **RPO (Recovery Point Objective)**
  - **Status:** CONCERNS ⚠️
  - **Threshold:** UNKNOWN
  - **Actual:** 原子 JSON 写入 (tmp→replace) 减少数据丢失风险，但无备份策略
  - **Evidence:** `multimodal_service.py:229-234` — 原子写入模式

---

## Maintainability Assessment

### Test Coverage

- **Status:** CONCERNS ⚠️
- **Threshold:** >=80% AC 覆盖率
- **Actual:** 13/24 AC 完全覆盖 (54%)，8 部分覆盖，4 缺失
- **Evidence:** `test-review-epic35-20260209.md` — 完整 AC 覆盖率矩阵
- **Findings:** 5/12 Stories 零后端测试覆盖 (35.4 MediaPanel, 35.5 Context Menu, 35.6 Audio, 35.7 Video, 35.11 Performance)。Mock service 测试提供约 15 个假覆盖率。

### Code Quality

- **Status:** PASS ✅
- **Threshold:** 代码结构清晰、异常处理完整
- **Actual:** 1564 行服务代码，结构清晰，自定义异常层次，依赖注入完整
- **Evidence:**
  - 服务代码: `multimodal_service.py` (1564 行) — 方法职责清晰
  - 模型代码: `multimodal_schemas.py` (387 行) — Pydantic 验证完整
  - API 代码: `endpoints/multimodal.py` (471 行) — RESTful 风格一致
  - 依赖注入: `dependencies.py:886-934` — 标准 FastAPI Depends 模式
- **Findings:** 代码质量是 EPIC-35 的优势。文件验证、错误处理、降级策略均体现了工程成熟度。

### Technical Debt

- **Status:** CONCERNS ⚠️
- **Threshold:** 无已知技术债务
- **Actual:** 多项已知技术债务
- **Evidence:**
  - E2E 条件断言 (8+ 处): `test_multimodal_workflow.py` — P0 级别
  - Mock service 测试: `test_multimodal.py:235-332` — 测试 Mock 而非真实服务
  - 5 个测试文件超 300 行限制 (最大 935 行)
  - 死代码 fixtures: `test_multimodal_workflow.py:185-265` (78 行未使用)
  - 废弃 API: `asyncio.get_event_loop().run_until_complete()` (4 处)
- **Findings:** 测试技术债务是最大风险。E2E 条件断言使 CI 管道失去回归检测能力。

### Documentation Completeness

- **Status:** PASS ✅
- **Threshold:** EPIC、Story、API 文档完整
- **Actual:** EPIC 文档完整，12 个 Story 文件存在，API 设计参考包含示例
- **Evidence:**
  - EPIC: `docs/epics/EPIC-35-MULTIMODAL-ACTIVATION.md` (334 行)
  - Stories: 12 个 story 文件 (`docs/stories/35.*.story.md`)
  - Pact 契约: `backend/tests/contract/pacts/canvas-frontend-canvas-backend-multimodal.json`
- **Findings:** 文档覆盖全面。EPIC 包含依赖图、API 设计参考、技术附录。

### Test Quality (from test-review, if available)

- **Status:** CONCERNS ⚠️
- **Threshold:** 测试质量 >= 70/100
- **Actual:** 54/100 (F 级)
- **Evidence:** `_bmad-output/test-artifacts/test-review-epic35-20260209.md`
- **Findings:** 18 个 HIGH 严重度违规。最严重: E2E 条件断言 (8+ 处)、Mock service 假覆盖率 (15 个)、5 个超长测试文件。积极面: 持久化测试优秀 (B+)、安全测试优秀 (B)。

---

## Custom NFR Assessments

### 数据完整性 (Data Integrity)

- **Status:** CONCERNS ⚠️
- **Threshold:** 双数据库一致性保证、原子操作
- **Actual:** JSON 持久化原子写入已验证；双数据库 (LanceDB + Neo4j) 原子性未测试
- **Evidence:**
  - 原子 JSON 写入: `multimodal_service.py:229-234` — tmp→replace 模式 ✅
  - 并发安全: `test_multimodal_real_persistence.py::test_concurrent_uploads_no_data_loss` ✅
  - 删除清理: `test_multimodal_workflow.py::test_delete_removes_from_concept_query` ✅
  - 缺失: 双数据库原子性测试 (LanceDB 成功 + Neo4j 失败时的回滚) ❌
  - 缺失: 孤儿文件检测和清理 ❌
  - 缺失: 一致性检查 (文件数 == JSON 索引数 == LanceDB 数) ❌
- **Findings:** 持久化层是 EPIC-35 测试的亮点，但双数据库原子性和一致性检查缺失是数据完整性风险。

### 可观测性 (Observability)

- **Status:** CONCERNS ⚠️
- **Threshold:** 结构化日志、健康检查、指标暴露
- **Actual:** 健康检查完整；降级日志存在；无 Prometheus 指标端点
- **Evidence:**
  - 健康检查: `GET /api/v1/multimodal/health` — 返回 status, storage_backend, vector_search_available, capability_level ✅
  - 降级日志: `multimodal_service.py:1314` — WARNING 级别降级通知 ✅
  - 延迟追踪: `test_rag_multimodal_integration.py::test_latency_tracking` — 分解追踪 (graphiti, lancedb, multimodal, fusion, reranking) ✅
  - 缺失: Prometheus/metrics 端点 ❌
  - 缺失: 分布式追踪/请求 ID ❌
  - 缺失: 审计日志 (谁/何时上传/删除了什么) ❌
- **Findings:** 健康检查和降级日志做得好，但缺少 Prometheus 指标和审计日志。

---

## Quick Wins

3 quick wins identified for immediate implementation:

1. **修复 E2E 条件断言** (Maintainability) - CRITICAL - 1 小时
   - 将 8+ 处 `if response.status_code == 201:` 替换为 `assert response.status_code == 201`
   - No code changes needed to production code / Minimal test code changes

2. **删除 E2E 死代码 fixtures** (Maintainability) - HIGH - 10 分钟
   - 删除 `test_multimodal_workflow.py:185-265` 中未使用的 `mock_lancedb_storage` 和 `mock_neo4j_driver`
   - No code changes needed to production code

3. **Singleton fixture 加 try/finally** (Reliability) - HIGH - 30 分钟
   - 所有 `reset_multimodal_service()` fixture 添加 `try/finally` 保护
   - No code changes needed to production code

---

## Recommended Actions

### Immediate (Before Release) - CRITICAL/HIGH Priority

1. **修复 E2E 测试条件断言模式** - CRITICAL - 1 小时 - Dev
   - 将所有 `if response.status_code ==` 替换为 `assert response.status_code ==`
   - 修复 8+ 处条件断言 in `test_multimodal_workflow.py`
   - Validation: 所有 E2E 测试在 API 失败时报告 FAIL 而非 PASS

2. **删除或重写 Mock Service 测试** - HIGH - 2 小时 - Dev
   - 删除 `TestMultimodalService` 和 `TestMultimodalQueryService` (测试 Mock 而非真实服务)
   - 或改为使用 `tmp_path` + 真实文件 I/O 测试真实 `MultimodalService`
   - Validation: 测试覆盖率反映真实代码行为

3. **补充 Story 35.6/35.7 基础测试** - HIGH - 4 小时 - Dev
   - AudioProcessor 和 VideoProcessor 的基本功能测试
   - Validation: 至少每个处理器 3 个测试 (元数据提取、格式支持、返回类型)

### Short-term (Next Sprint) - MEDIUM Priority

1. **添加大文件上传测试** - MEDIUM - 2 小时 - Dev
   - 使用 50MB 测试文件验证 AC 35.9.5 合规性
   - 添加 50MB+ 文件拒绝测试 (验证 413 响应)

2. **实现运行时 Pact Provider Verification** - MEDIUM - 4 小时 - Dev
   - 启动 FastAPI → 发送 HTTP → 验证响应 (替代当前静态 JSON 分析)

3. **定义性能 SLO** - MEDIUM - 1 小时 - Team
   - 定义 P95/P99 延迟目标、吞吐量目标、内存使用限制

4. **添加 MIME 欺骗测试** - MEDIUM - 2 小时 - Dev
   - 测试 `.exe` 伪装为 `.png` 的检测能力

### Long-term (Backlog) - LOW Priority

1. **添加认证层** - LOW - 8 小时 - Dev
   - 如果后端将暴露到网络，添加 JWT/API Key 认证
   - 当前本地场景可接受无认证

2. **实现 Prometheus 指标端点** - LOW - 4 小时 - Dev
   - 暴露 upload_count, upload_size_bytes, search_latency_seconds 指标

3. **添加审计日志** - LOW - 4 小时 - Dev
   - 记录所有上传/删除/更新操作的审计日志

---

## Monitoring Hooks

4 monitoring hooks recommended to detect issues before failures:

### Performance Monitoring

- [ ] 添加 upload 延迟追踪 — 记录每次上传的处理时间，设置 5 秒告警阈值
  - **Owner:** Dev
  - **Deadline:** Next Sprint

- [ ] 添加存储空间监控 — 监控 `.canvas-learning/multimodal/` 目录大小
  - **Owner:** Dev
  - **Deadline:** Next Sprint

### Security Monitoring

- [ ] 添加文件验证失败计数器 — 检测异常上传尝试模式 (可能攻击)
  - **Owner:** Dev
  - **Deadline:** Backlog

### Reliability Monitoring

- [ ] 健康检查定期轮询 — 每 60 秒调用 `GET /api/v1/multimodal/health`
  - **Owner:** Ops
  - **Deadline:** Next Sprint

### Alerting Thresholds

- [ ] 搜索降级告警 — 当 `capability_level == "degraded"` 持续 > 5 分钟时通知
  - **Owner:** Ops
  - **Deadline:** Next Sprint

---

## Fail-Fast Mechanisms

3 fail-fast mechanisms recommended to prevent failures:

### Circuit Breakers (Reliability)

- [ ] Embedding 服务熔断 — 当前已有重试机制 (2 次, 2 秒延迟)。建议添加：连续失败 5 次后暂停 embedding 调用 60 秒，自动降级为文本搜索。
  - **Owner:** Dev
  - **Estimated Effort:** 2 小时

### Rate Limiting (Performance)

- [ ] 上传速率限制 — 每用户每分钟最多 10 次上传，防止滥用或误操作
  - **Owner:** Dev
  - **Estimated Effort:** 2 小时

### Validation Gates (Security)

- [ ] 已实现: MIME + Magic Bytes + 大小 + 路径遍历 + SSRF 多层验证 ✅

### Smoke Tests (Maintainability)

- [ ] 部署后冒烟测试 — 上传 1 张图片 → 搜索 → 删除，验证端到端功能
  - **Owner:** Dev
  - **Estimated Effort:** 1 小时

---

## Evidence Gaps

7 evidence gaps identified - action required:

- [ ] **性能 P95/P99 延迟** (Performance)
  - **Owner:** Dev
  - **Deadline:** Next Sprint
  - **Suggested Evidence:** k6 负载测试报告 / pytest-benchmark 输出
  - **Impact:** 无法判断性能是否满足生产要求

- [ ] **大文件上传测试** (Performance)
  - **Owner:** Dev
  - **Deadline:** Before Release
  - **Suggested Evidence:** 50MB PNG, 500MB MP4 上传测试结果
  - **Impact:** AC 35.9.5 合规性无法确认

- [ ] **认证/授权测试** (Security)
  - **Owner:** Dev
  - **Deadline:** If exposing to network
  - **Suggested Evidence:** JWT/OAuth 端到端测试
  - **Impact:** 网络暴露场景下有安全风险

- [ ] **双数据库原子性测试** (Data Integrity)
  - **Owner:** Dev
  - **Deadline:** Next Sprint
  - **Suggested Evidence:** LanceDB 成功 + Neo4j 失败时的回滚验证
  - **Impact:** 数据不一致风险

- [ ] **灾难恢复 RTO/RPO** (Disaster Recovery)
  - **Owner:** Team
  - **Deadline:** Before GA
  - **Suggested Evidence:** 恢复时间测量、备份策略文档
  - **Impact:** 数据丢失风险

- [ ] **CI Burn-In 结果** (Reliability)
  - **Owner:** Dev
  - **Deadline:** Before Release
  - **Suggested Evidence:** 100+ 次连续成功运行记录
  - **Impact:** 测试稳定性无法保证

- [ ] **Prometheus 指标** (Observability)
  - **Owner:** Dev
  - **Deadline:** Backlog
  - **Suggested Evidence:** /metrics 端点暴露 RED 指标
  - **Impact:** 生产监控盲区

---

## Findings Summary

**Based on ADR Quality Readiness Checklist (8 categories, 29 criteria)**

| Category                                         | Criteria Met | PASS | CONCERNS | FAIL | Overall Status        |
| ------------------------------------------------ | ------------ | ---- | -------- | ---- | --------------------- |
| 1. Testability & Automation                      | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️          |
| 2. Test Data Strategy                            | 2/3          | 2    | 1        | 0    | CONCERNS ⚠️          |
| 3. Scalability & Availability                    | 1/4          | 1    | 3        | 0    | CONCERNS ⚠️          |
| 4. Disaster Recovery                             | 0/3          | 0    | 3        | 0    | CONCERNS ⚠️          |
| 5. Security                                      | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️          |
| 6. Monitorability, Debuggability & Manageability | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️          |
| 7. QoS & QoE                                     | 2/4          | 2    | 2        | 0    | CONCERNS ⚠️          |
| 8. Deployability                                 | 2/3          | 2    | 1        | 0    | PASS ✅               |
| **Total**                                        | **13/29**    | **13** | **16** | **0** | **CONCERNS ⚠️**     |

**Criteria Met Scoring:**

- ≥26/29 (90%+) = Strong foundation
- 20-25/29 (69-86%) = Room for improvement
- <20/29 (<69%) = Significant gaps

**Current: 13/29 (45%) = Significant gaps** — 但无 FAIL 级阻塞问题

---

### ADR Checklist Detail

#### 1. Testability & Automation (2/4)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 1.1 | Isolation: Mock downstream deps | ⚠️ | E2E 条件断言静默跳过；Mock service 测试假覆盖 | 修复条件断言 |
| 1.2 | Headless: 100% via API | ✅ | 8 个 REST API 端点全面覆盖 | — |
| 1.3 | State Control: Seeding APIs | ⚠️ | 无测试数据 seeding API；依赖 JSON 文件 | 考虑 test data API |
| 1.4 | Sample Requests: cURL examples | ✅ | Pact 契约文件包含 10 个交互定义 | — |

#### 2. Test Data Strategy (2/3)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 2.1 | Segregation: Test data isolation | ✅ | `tmp_path` 隔离，独立存储路径 | — |
| 2.2 | Generation: Synthetic data | ✅ | `make_minimal_png()`, `make_minimal_pdf()` 工厂 | — |
| 2.3 | Teardown: Cleanup | ⚠️ | Singleton reset 无 try/finally (泄漏风险) | 添加 try/finally |

#### 3. Scalability & Availability (1/4)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 3.1 | Statelessness | ⚠️ | Singleton + 内存 `_content_store` | 不支持水平扩展 |
| 3.2 | Bottlenecks identified | ⚠️ | 无负载测试 | 需要 k6 测试 |
| 3.3 | SLA Definitions | ⚠️ | 仅 "10 images < 5s" | 需要正式 SLO |
| 3.4 | Circuit Breakers | ✅ | Embedding 重试 + 降级到文本搜索 | — |

#### 4. Disaster Recovery (0/3)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 4.1 | RTO/RPO defined | ⚠️ | 未定义 | 定义恢复目标 |
| 4.2 | Failover tested | ⚠️ | 重启恢复已测试，无多实例 failover | — |
| 4.3 | Backups immutable | ⚠️ | 原子 JSON 写入，无备份策略 | 定义备份策略 |

#### 5. Security (2/4)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 5.1 | AuthN/AuthZ | ⚠️ | 无认证 (本地场景设计决策) | 网络暴露需添加 |
| 5.2 | Encryption | ⚠️ | 明文存储，HTTP 传输 | 本地可接受 |
| 5.3 | Secrets management | ✅ | 环境变量配置，无硬编码 | — |
| 5.4 | Input Validation | ✅ | MIME + Magic Bytes + 大小 + 路径遍历 + SSRF | — |

#### 6. Monitorability (2/4)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 6.1 | Tracing | ⚠️ | 无分布式追踪/请求 ID | 添加 correlation ID |
| 6.2 | Logs | ✅ | 降级 WARNING、错误日志完整 | — |
| 6.3 | Metrics | ⚠️ | 无 Prometheus/metrics 端点 | 添加 RED 指标 |
| 6.4 | Config externalized | ✅ | `MULTIMODAL_MAX_FILE_SIZE_MB` 环境变量 | — |

#### 7. QoS & QoE (2/4)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 7.1 | Latency targets | ⚠️ | 无 P95/P99 SLO | 定义 SLO |
| 7.2 | Rate Limiting | ⚠️ | 无速率限制 | 添加 rate limiting |
| 7.3 | Perceived Performance | ✅ | MediaPanel 加载状态/错误状态 UI | — |
| 7.4 | Degradation UX | ✅ | "当前使用关键字搜索" 降级通知 | — |

#### 8. Deployability (2/3)

| # | Criterion | Status | Evidence | Gap |
|---|-----------|--------|----------|-----|
| 8.1 | Zero Downtime | ⚠️ | 无 blue/green 策略 | 本地场景不需要 |
| 8.2 | Backward Compatibility | ✅ | 新端点不修改现有 API | — |
| 8.3 | Rollback | ✅ | EPIC 明确回滚计划 (移除路由注册) | — |

---

## Gate YAML Snippet

```yaml
nfr_assessment:
  date: '2026-02-10'
  story_id: 'EPIC-35'
  feature_name: '多模态功能完整激活 (Multimodal Activation)'
  adr_checklist_score: '13/29'
  categories:
    testability_automation: 'CONCERNS'
    test_data_strategy: 'CONCERNS'
    scalability_availability: 'CONCERNS'
    disaster_recovery: 'CONCERNS'
    security: 'CONCERNS'
    monitorability: 'CONCERNS'
    qos_qoe: 'CONCERNS'
    deployability: 'PASS'
  overall_status: 'CONCERNS'
  critical_issues: 0
  high_priority_issues: 5
  medium_priority_issues: 4
  concerns: 16
  blockers: false
  quick_wins: 3
  evidence_gaps: 7
  recommendations:
    - '修复 E2E 测试条件断言模式 (P0 - 1小时)'
    - '删除或重写 Mock Service 测试 (HIGH - 2小时)'
    - '补充 Story 35.6/35.7 基础测试 (HIGH - 4小时)'
    - '添加大文件上传测试 (MEDIUM - 2小时)'
    - '定义性能 SLO (MEDIUM - 1小时)'
```

---

## Related Artifacts

- **EPIC File:** `docs/epics/EPIC-35-MULTIMODAL-ACTIVATION.md`
- **Story Files:** `docs/stories/35.{1-12}.story.md` (12 个文件)
- **Test Review:** `_bmad-output/test-artifacts/test-review-epic35-20260209.md`
- **Previous NFR Assessment:** `_bmad-output/test-artifacts/nfr-assessment-epic35.md` (2026-02-09, v1.0)
- **Evidence Sources:**
  - Test Results: `backend/tests/` (12 个 multimodal 测试文件)
  - Service Code: `backend/app/services/multimodal_service.py` (1564 行)
  - API Code: `backend/app/api/v1/endpoints/multimodal.py` (471 行)
  - Schema Code: `backend/app/models/multimodal_schemas.py` (387 行)
  - Frontend: `canvas-progress-tracker/obsidian-plugin/src/components/MediaPanel.ts`
  - Pact Contract: `backend/tests/contract/pacts/canvas-frontend-canvas-backend-multimodal.json`

---

## Recommendations Summary

**Release Blocker:** 无 — 无 FAIL 级问题。所有 CONCERNS 均为可控风险。

**High Priority:** 修复 E2E 测试条件断言 (CI 管道可靠性)、重写 Mock service 测试 (消除假覆盖率)、补充 Audio/Video 处理器测试

**Medium Priority:** 大文件测试、Pact Provider Verification、性能 SLO 定义、MIME 欺骗测试

**Next Steps:**
1. 修复 3 个 Quick Wins (累计 ~1.5 小时)
2. 完成 3 个 HIGH 优先级行动 (累计 ~8 小时)
3. 重新运行 `testarch-nfr` 评估以验证改进

---

## Sign-Off

**NFR Assessment:**

- Overall Status: CONCERNS ⚠️
- Critical Issues: 0
- High Priority Issues: 5
- Concerns: 16/29 criteria
- Evidence Gaps: 7

**Gate Status:** CONCERNS ⚠️

**Next Actions:**

- If PASS ✅: Proceed to `*gate` workflow or release
- If CONCERNS ⚠️: Address HIGH/CRITICAL issues, re-run `*nfr-assess`
- If FAIL ❌: Resolve FAIL status NFRs, re-run `*nfr-assess`

**Current recommendation:** ⚠️ CONCERNS — 修复 HIGH 优先级测试问题后重新评估。代码实现质量良好（安全验证、降级策略、错误处理），但测试结构缺陷（条件断言、假覆盖率）削弱了信心。

**Generated:** 2026-02-10
**Workflow:** testarch-nfr v5.0 (ADR Quality Readiness Checklist)
**Supersedes:** nfr-assessment-epic35.md v1.0 (2026-02-09)

---

<!-- Powered by BMAD-CORE™ -->
